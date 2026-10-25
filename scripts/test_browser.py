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
        document.addEventListener('DOMContentLoaded', () => setTimeout(async () => {
            const p = document.createElement('p'); p.id = 'dynamic-ad';
            p.style.opacity = '0'; p.textContent = 'Runtime text'; document.body.append(p);
            const response = await fetch('/fixtures/comment');
            document.body.insertAdjacentHTML('beforeend', await response.text());
            const link = document.createElement('a'); link.href='/fixtures/runtime-child';
            link.textContent = 'Child'; document.body.append(link);
            for (const number of [1, 2]) {
                const frame = document.createElement('iframe'); frame.src='/fixtures/runtime-frame';
                frame.onload = () => {
                    const ad = frame.contentDocument.createElement('p');
                    ad.id='parent-ad'; ad.style.opacity='0'; ad.textContent='Insertion ' + number;
                    frame.contentDocument.body.append(ad);
                };
                document.body.append(frame);
            }
            const inline = document.createElement('iframe'); inline.id='inline';
            inline.srcdoc = `<body onload="const p=document.createElement('p');p.id='inline-ad';p.style.opacity='0';p.textContent='Inline runtime';document.body.append(p)">`;
            document.body.append(inline);
            const blank = document.createElement('iframe'); blank.id='blank';
            blank.onload = () => blank.contentDocument.body.innerHTML = '<p id="blank-ad" style="opacity:0">Blank runtime</p>';
            document.body.append(blank);
        }, 50));
        </script><body></body>''',
    "comment": '<p id="comment" style="opacity:0">Fetched comment</p>',
    "runtime-frame": '''<!doctype html><body><script>
        const p=document.createElement('p'); p.id='frame-ad'; p.style.opacity='0';
        p.textContent='Frame runtime'; document.body.append(p);
        const frame=document.createElement('iframe'); frame.src='/fixtures/runtime-nested'; document.body.append(frame);
        </script>''',
    "runtime-nested": '<body onload="document.querySelector(\'p\').style.opacity=\'0\'"><p id="nested-ad">Nested runtime</p>',
    "runtime-child": '<body onload="document.querySelector(\'p\').style.opacity=\'0\'"><p id="child-ad">Child runtime</p>',
    "runtime-error": '<body><p style="opacity:0">Surviving result</p><iframe src="/fixtures/missing"></iframe><script>throw new Error("Fixture runtime error")</script>',
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
                    target.wait_for_selector('#dynamic-ad', state='attached')
                    assert dynamic['findings'] == [], 'Static collection contract changed'
                    page.locator('#collectionMode').select_option('browser')
                    runtime = analyze('dynamic')
                    assert runtime['collection_mode'] == 'browser'
                    assert len(runtime['findings']) == 11, runtime
                    assert not runtime['warnings'], runtime['warnings']
                    assert json.loads(main.result_path.read_text(encoding='utf-8')) == runtime['result_json']
                    assert json.loads(page.locator('#output').inner_text())['collectionMode'] == 'browser'
                    assert any('Fetched comment' in f['evidence'] for f in runtime['findings'])
                    assert any('Insertion 1' in f['evidence'] for f in runtime['findings'])
                    assert any('Insertion 2' in f['evidence'] for f in runtime['findings'])
                    assert any('Child runtime' in f['evidence'] for f in runtime['findings'])
                    # Locate each finding from its exported top URL in a fresh browser page.
                    current_url = None
                    for finding in runtime['findings']:
                        if current_url != finding['url']:
                            target.goto(finding['url'])
                            target.wait_for_timeout(500)
                            current_url = finding['url']
                        context = target.main_frame
                        segments = finding['location'].split(' >>> ')
                        for selector in segments[:-1]:
                            element = context.query_selector(selector)
                            assert element is not None, finding
                            context = element.content_frame()
                            assert context is not None, finding
                        element = context.locator(segments[-1])
                        assert element.count() == 1, finding
                        assert element.text_content().strip() in finding['evidence'], finding
                    shallow_response = page.request.post(base + '/api/analyze', data={
                        'url': base + '/fixtures/dynamic', 'collection_mode': 'browser', 'max_depth': 0,
                    })
                    assert shallow_response.status == 200, shallow_response.text()
                    shallow = shallow_response.json()
                    assert len(shallow['findings']) == 10, shallow
                    assert any('max_depth=0' in warning for warning in shallow['warnings'])
                    partial = analyze('runtime-error')
                    assert len(partial['findings']) == 1
                    assert any('Fixture runtime error' in warning for warning in partial['warnings'])
                    assert any('수집 실패' in warning for warning in partial['warnings'])
                    assert '일부 범위 미분석' in page.locator('#status').inner_text()
                    previous = main.result_path.read_bytes()
                    analyze('missing', 502)
                    assert main.result_path.read_bytes() == previous
                    clean = analyze('clean')
                    assert clean['findings'] == [] and clean['collection_mode'] == 'browser'
                    # Startup and waiting both share the analysis deadline.
                    previous = main.result_path.read_bytes()
                    expired = page.request.post(base + '/api/analyze', data={
                        'url': base + '/fixtures/dynamic', 'collection_mode': 'browser',
                        'total_timeout_sec': 0.1, 'render_wait_ms': 5000,
                    })
                    assert expired.status == 504, expired.text()
                    assert main.result_path.read_bytes() == previous
                    assert not errors, errors
                    print(f'Browser checks passed: Edge {browser.version}; UI, filters, partial results, failure recovery, empty results')
                    print('Dynamic checks passed: static=0/browser=11; fetched comments, runtime links/depth, live repeated/nested frames, scripted srcdoc/about:blank, locations, file, JS/frame failure warnings, 502/504 preservation')
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            sock.close()
            main.result_path = original_result_path
            if thread.is_alive():
                raise RuntimeError('Local test server did not stop')


if __name__ == '__main__':
    run()
