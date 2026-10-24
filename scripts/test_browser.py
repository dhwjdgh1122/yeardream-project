"""Run real Edge checks against a temporary local server (requires Playwright)."""

import json
import socket
import sys
import tempfile
import threading
import time
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app import main


DOCUMENTS = {
    "root": '''<!doctype html><title>Browser fixture</title>
        <p id="ad:1" style="opacity:0">Root transparent</p>
        <p id="jamo">ㄱㄴㄷ</p><p id="homoglyph">аbc</p>
        <p style="position:absolute;left:-9999px">Outside</p>
        <table><tr><td class="ad" style="opacity:0">Table first</td></tr></table>
        <table><tr><td class="ad" style="opacity:0">Table second</td></tr></table>
        <iframe src="/fixtures/shared"></iframe><iframe src="/fixtures/shared"></iframe>
        <iframe srcdoc="&lt;p style='opacity:0'&gt;Inline frame&lt;/p&gt;"></iframe>
        <iframe></iframe>''',
    "shared": '<iframe src="/fixtures/nested"></iframe>',
    "nested": '<p id="nested:ad" style="opacity:0">Nested transparent</p>',
    "clean": '<!doctype html><title>Clean</title><p>Normal text</p>',
    "dynamic": '''<!doctype html><title>Dynamic</title><script>
        const p = document.createElement('p'); p.id = 'dynamic-ad';
        p.style.opacity = '0'; p.textContent = 'Runtime text';
        document.addEventListener('DOMContentLoaded', () => document.body.append(p));
        </script><body></body>''',
}


def run():
    fixture_app = FastAPI()

    @fixture_app.get('/fixtures/{name}', response_class=HTMLResponse)
    def fixture(name: str):
        return HTMLResponse(DOCUMENTS[name]) if name in DOCUMENTS else HTMLResponse('', status_code=404)

    fixture_app.mount('/', main.app)
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    base = f'http://127.0.0.1:{sock.getsockname()[1]}'
    server = uvicorn.Server(uvicorn.Config(fixture_app, log_level='error', lifespan='off'))
    thread = threading.Thread(target=server.run, kwargs={'sockets': [sock]}, daemon=True)
    original_result_path = main.result_path
    with tempfile.TemporaryDirectory(prefix='yeardream-browser-') as temporary:
        main.result_path = Path(temporary) / 'result.json'
        try:
            thread.start()
            limit = time.monotonic() + 10
            while not server.started:
                if not thread.is_alive() or time.monotonic() >= limit:
                    raise RuntimeError('Local test server did not start')
                time.sleep(0.05)
            with sync_playwright() as playwright:
                with playwright.chromium.launch(channel='msedge', headless=True) as browser:
                    page = browser.new_page()
                    errors = []
                    page.on('pageerror', lambda error: errors.append(str(error)))
                    page.goto(base)

                    def analyze(name, expected_status=200):
                        page.locator('#url').fill(f'{base}/fixtures/{name}')
                        with page.expect_response(lambda response: response.url == base + '/api/analyze') as pending:
                            page.locator('#analyze').click()
                        response = pending.value
                        assert response.status == expected_status, response.text()
                        page.wait_for_function("!document.querySelector('#analyze').disabled")
                        return response.json()

                    data = analyze('root')
                    assert len(data['findings']) == 9, data
                    assert data['warnings'] and '일부 범위 미분석' in page.locator('#status').inner_text()
                    assert json.loads(main.result_path.read_text(encoding='utf-8')) == data['result_json']
                    target = browser.new_page()
                    target.goto(base + '/fixtures/root')
                    for finding in data['findings']:
                        context = target.main_frame
                        segments = finding['location'].split(' >>> ')
                        for selector in segments[:-1]:
                            frame_element = context.locator(selector)
                            assert frame_element.count() == 1, finding
                            context = frame_element.element_handle().content_frame()
                            assert context is not None, finding
                        element = context.locator(segments[-1])
                        assert element.count() == 1, finding
                        assert element.text_content().strip() in finding['evidence'], finding
                    print('Browser locations passed: tables, escaped IDs, repeated/nested frames, srcdoc')
                    for technique in ['HOMOGLYPH', 'JAMO', 'TRANSPARENT', 'OFFSCREEN', 'ALL']:
                        page.locator('#techniqueFilter').select_option(technique)
                        summary = json.loads(page.locator('#output').inner_text())
                        expected = [f for f in data['findings'] if technique == 'ALL' or f['technique'] == technique]
                        assert summary['totalFindings'] == len(expected)
                        assert all(f['evidence'] for f in summary['findings'])
                    previous = main.result_path.read_bytes()
                    analyze('missing', 502)
                    assert page.locator('#status').inner_text() == '오류 발생'
                    assert main.result_path.read_bytes() == previous
                    page.locator('#techniqueFilter').select_option('ALL')
                    assert '수집하지 못했습니다' in page.locator('#output').inner_text()
                    clean = analyze('clean')
                    assert clean['findings'] == [] and not clean['warnings']
                    assert '분석 완료: 0개' in page.locator('#status').inner_text()
                    dynamic = analyze('dynamic')
                    target.goto(base + '/fixtures/dynamic')
                    assert target.locator('#dynamic-ad').count() == 1
                    assert dynamic['findings'] == [], 'Static collection contract changed'
                    assert not errors, errors
                    print(f'Browser checks passed: Edge {browser.version}; UI, filters, partial results, failure recovery, empty results')
                    print('Dynamic limitation confirmed: runtime element exists in browser but is absent from static findings')
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            sock.close()
            main.result_path = original_result_path
            if thread.is_alive():
                raise RuntimeError('Local test server did not stop')


if __name__ == '__main__':
    run()
