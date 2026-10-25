"""Exercise a copied Windows executable with local fixtures and real Edge."""

import argparse
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from playwright.sync_api import sync_playwright


class FixtureHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        documents = {
            '/static': '<p id="ad" style="opacity:0">카지노 가입 보너스</p><p style="opacity:0">메뉴</p>',
            '/dynamic': '''<!doctype html><style>.hidden{opacity:0}</style><body><script>
                document.addEventListener('DOMContentLoaded', () => {
                  const p=document.createElement('p'); p.id='runtime';p.className='hidden';
                  p.textContent='성인영상 무료시청';document.body.append(p);
                });</script></body>''',
            '/clean': '<p>정상 안내</p>',
            '/chat': '<p>Google 강좌 수료 후 받은 우산 후기. 구글 직원인 줄 알려나? ㅋㅋ</p>',
            '/search-ad': '<p>먹튀검증 구글검색 커뮤니티A</p>',
            '/search-warning': '<p>토토사이트 구글검색을 하지 마세요.</p>',
        }
        self.send_response(200 if self.path in documents else 500)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(documents.get(self.path, 'Fixture failure').encode('utf-8'))

    def log_message(self, *args):
        pass


def request_json(address, payload=None):
    data = json.dumps(payload).encode('utf-8') if payload is not None else None
    request = Request(address, data=data, headers={'Content-Type': 'application/json'})
    with urlopen(request, timeout=70) as response:
        return json.load(response)


def check_files(bundle, data):
    assert json.loads((bundle / 'result.json').read_bytes()) == data['result_json']
    assert json.loads((bundle / 'result_extra.json').read_bytes()) == data['result_extra_json']


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle', type=Path)
    parser.add_argument('--report', type=Path, help='Optional new report file; never overwrite')
    args = parser.parse_args()
    original = args.bundle.resolve()
    if args.report and args.report.exists():
        parser.error('Report already exists')
    manifest_raw = (original / 'build-manifest.json').read_bytes()
    manifest = json.loads(manifest_raw)
    for name, expected in manifest['bundle_sha256'].items():
        path = (original / name).resolve()
        assert path.is_relative_to(original), 'Invalid manifest path'
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name
    fixture = ThreadingHTTPServer(('127.0.0.1', 0), FixtureHandler)
    threading.Thread(target=fixture.serve_forever, daemon=True).start()
    fixture_base = f'http://127.0.0.1:{fixture.server_port}'
    try:
        with tempfile.TemporaryDirectory(prefix='yeardream-packaged-') as tmp:
            directory = Path(tmp)
            bundle = directory / '한글 배포 폴더' / 'YearDream'
            shutil.copytree(original, bundle)
            working = directory / 'unrelated working directory'
            working.mkdir()
            environment = os.environ.copy()
            for key in ('PYTHONPATH', 'PYTHONHOME', 'VIRTUAL_ENV'):
                environment.pop(key, None)
            environment['PATH'] = str(Path(os.environ['SystemRoot']) / 'System32')
            # Reserve a port to verify that a second instance reports a conflict.
            with socket.socket() as reserved:
                reserved.bind(('127.0.0.1', 0))
                reserved.listen()
                collision = subprocess.run(
                    [str(bundle / 'YearDream.exe'), '--no-browser', '--port', str(reserved.getsockname()[1])],
                    cwd=working, env=environment, capture_output=True, timeout=30,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                assert collision.returncode == 1 and b'Cannot start YearDream' in collision.stdout
            with tempfile.TemporaryFile() as log:
                process = subprocess.Popen(
                    [str(bundle / 'YearDream.exe'), '--no-browser', '--port', '0'],
                    cwd=working, env=environment, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                try:
                    deadline = time.monotonic() + 30
                    base = None
                    while time.monotonic() < deadline:
                        log.seek(0)
                        output = log.read().decode('utf-8', errors='replace')
                        for line in output.splitlines():
                            if line.startswith('YearDream: '):
                                base = line.removeprefix('YearDream: ').strip()
                        if base:
                            try:
                                assert request_json(base + '/api/health') == {'status': 'ok'}
                                break
                            except (URLError, TimeoutError):
                                pass
                        if process.poll() is not None:
                            raise RuntimeError(output)
                        time.sleep(0.1)
                    else:
                        raise RuntimeError('Packaged server did not start:\n' + output)
                    with urlopen(base, timeout=5) as response:
                        assert 'JSON 다운로드' in response.read().decode('utf-8')
                    assert '/api/analyze' in request_json(base + '/openapi.json')['paths']
                    data = request_json(base + '/api/analyze', {'url': fixture_base + '/static', 'max_depth': 0})
                    assert len(data['findings']) == 2 and len(data['result_json']['findings']) == 1
                    assert all('confidence' not in item and item['source_text'] for item in data['findings'])
                    check_files(bundle, data)
                    before = {name: (bundle / name).read_bytes() for name in ('result.json', 'result_extra.json')}
                    for payload, status in [({'url': fixture_base, 'collection_mode': 'invalid'}, 422),
                                            ({'url': fixture_base + '/failure'}, 502)]:
                        try:
                            request_json(base + '/api/analyze', payload)
                            raise AssertionError('Expected a failed request')
                        except HTTPError as error:
                            assert error.code == status
                        assert before == {name: (bundle / name).read_bytes() for name in before}
                    static = request_json(base + '/api/analyze', {'url': fixture_base + '/dynamic', 'max_depth': 0})
                    assert static['findings'] == []
                    # UI and the packaged backend each launch their own Edge context.
                    with sync_playwright() as playwright:
                        browser = playwright.chromium.launch(channel='msedge', headless=True)
                        try:
                            page = browser.new_page(accept_downloads=True)
                            page.goto(base)
                            page.locator('#url').fill(fixture_base + '/dynamic')
                            page.locator('#collectionMode').select_option('browser')
                            with page.expect_response('**/api/analyze', timeout=70000) as response:
                                page.locator('#analyze').click()
                            assert response.value.status == 200, response.value.text()
                            dynamic = response.value.json()
                            assert {f['technique'] for f in dynamic['result_json']['findings']} == {'TRANSPARENT'}
                            assert dynamic['result_json']['findings'][0]['evidence_text'] == '성인영상 무료시청'
                            assert page.locator('#findingCards article').count() == 1
                            assert page.locator('#rawDetails').get_attribute('open') is None
                            check_files(bundle, dynamic)
                            for button, key in [('#download', 'result_json'), ('#downloadExtra', 'result_extra_json')]:
                                with page.expect_download() as download:
                                    page.locator(button).click()
                                assert json.loads(Path(download.value.path()).read_bytes()) == dynamic[key]
                        finally:
                            browser.close()
                    chat = request_json(base + '/api/analyze', {'url': fixture_base + '/chat', 'max_depth': 0})
                    assert chat['findings'] == [] and chat['content_candidates'] == []
                    check_files(bundle, chat)
                    search = request_json(base + '/api/analyze', {'url': fixture_base + '/search-ad', 'max_depth': 0})
                    assert len(search['content_candidates']) == 1
                    assert search['content_policy_version'] == 'content-rules-v5'
                    assert search['result_json']['findings'] == []
                    check_files(bundle, search)
                    warning = request_json(base + '/api/analyze', {'url': fixture_base + '/search-warning', 'max_depth': 0})
                    assert warning['content_candidates'] == []
                    clean = request_json(base + '/api/analyze', {'url': fixture_base + '/clean', 'max_depth': 0})
                    assert clean['result_json']['findings'] == clean['result_extra_json']['findings'] == []
                    check_files(bundle, clean)
                    assert not (working / 'result.json').exists()
                    assert not (working / 'result_extra.json').exists()
                finally:
                    process.terminate()
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)
    finally:
        fixture.shutdown()
        fixture.server_close()
    report = {
        'status': 'passed', 'scope': 'Local synthetic fixtures on the build PC; not other-PC or real-site accuracy',
        'executable_sha256': manifest['bundle_sha256']['YearDream.exe'],
        'manifest_sha256': hashlib.sha256(manifest_raw).hexdigest(),
        'checks': ['bundle hashes', 'Korean/spaced path', 'unrelated cwd', 'Python removed from PATH',
                   'health/UI/OpenAPI', 'port collision', 'static selection', 'failure preserves files',
                   'packaged Edge JS/computed CSS', 'readable cards/collapsed JSON', 'no uncalibrated confidence',
                   'chat laughter excluded', 'search promotion vs prohibition', 'UI downloads', 'empty results', 'output beside exe'],
    }
    if args.report:
        with args.report.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
    print(json.dumps(report))


if __name__ == '__main__':
    run()
