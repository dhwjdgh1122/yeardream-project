"""Run real Edge checks against a temporary local server (requires Playwright)."""

import json
import socket
import subprocess
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
from backend.app.evaluation import evaluate_capture


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
    "content": '''<p id="gamble">토토사이트 신규가입 보너스 안내</p>
        <p id="adult">야동티비 무료시청 플랫폼</p>
        <p id="education">도박 예방교육: 토토사이트 가입 보너스 광고를 주의하세요.</p>''',
    "computed": '''<!doctype html><link rel="stylesheet" href="/fixtures/css-rules"><style>
        .opacity {opacity:0} .same {color:rgb(12,34,56);background:rgb(12,34,56)}
        .none {display:none} .tiny {font-size:1px}
        .outside {position:absolute;left:-9999px;width:100px}
        .alpha {color:rgba(1,2,3,0)} .hidden {visibility:hidden}
        #overridden {opacity:1 !important}
        </style><p id="opacity" class="opacity">Class opacity</p>
        <p id="same" class="same">카지노 가입 보너스</p>
        <div class="none"><p id="display-child">Hidden parent</p></div>
        <div class="tiny"><p id="tiny-child">Small inherited font</p></div>
        <p id="outside" class="outside">Negative rectangle</p>
        <p id="alpha" class="alpha">Transparent RGB</p>
        <div class="hidden"><p id="hidden-child">Inherited visibility</p></div>
        <p id="external" class="external">External stylesheet</p>
        <p id="overridden" style="opacity:0">Visible override</p>
        <p id="partial" style="position:absolute;left:-1px;width:200px">Partly visible</p>
        <p id="below" style="position:absolute;top:3000px">Below fold</p>
        <p id="shadow" style="color:white;background:white;text-shadow:1px 1px black">Visible shadow</p>
        <p id="stroke" style="color:transparent;-webkit-text-stroke:1px black">Visible stroke</p>
        <iframe id="styled-frame" src="/fixtures/computed-child"></iframe>''',
    "computed-child": '<style>.frame-style{opacity:0}</style><p id="frame-style" class="frame-style">Styled frame</p>',
    "css-rules": '.external {color:transparent}',
    "policy": '''<style>.policy-hidden{opacity:0}</style>
        <p id="policy-jamo">ㅋㅏㅈㅣㄴㅗ ㅂㅗㄴㅓㅅㅡ</p>
        <p id="policy-homoglyph">ｍｅｇａ－ＢＥＴ 첫충 30％ 지급</p>
        <p id="policy-transparent" class="policy-hidden">카지노 가입 보너스</p>
        <p id="policy-offscreen" style="font-size:1px">성인영상 무료시청</p>
        <p id="policy-menu" class="policy-hidden">메뉴 열기</p>
        <p id="policy-foreign">Привет &lt;img src=x onerror="window.__injected=true"&gt;</p><p id="policy-chat">ㅋㅋ 반가워</p>
        <p>카지노 가입 보너스. <span id="policy-unrelated" class="policy-hidden">메뉴</span></p>''',
}


def run():
    fixture_app = FastAPI()

    @fixture_app.get('/fixtures/{name}', response_class=HTMLResponse)
    def fixture(name: str):
        return (HTMLResponse(DOCUMENTS[name], media_type='text/css' if name == 'css-rules' else 'text/html')
                if name in DOCUMENTS else HTMLResponse('', status_code=404))

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
                    assert page.locator('#download').is_disabled()
                    assert page.locator('#downloadContent').is_disabled()
                    assert page.locator('#downloadExtra').is_disabled()

                    def download_json(data, name):
                        with page.expect_download() as pending:
                            page.locator('#download').click()
                        download = pending.value
                        assert download.suggested_filename == 'result.json'
                        path = Path(temporary) / f'{name}.json'
                        download.save_as(path)
                        raw = path.read_bytes()
                        assert not raw.startswith(b'\xef\xbb\xbf')
                        assert json.loads(raw.decode('utf-8')) == data['result_json']
                        assert data['result_json']['meta']['topic'] == 'TOPIC'
                        with page.expect_download() as pending_extra:
                            page.locator('#downloadExtra').click()
                        extra_download = pending_extra.value
                        assert extra_download.suggested_filename == 'result_extra.json'
                        extra_path = Path(temporary) / f'{name}.extra.json'
                        extra_download.save_as(extra_path)
                        extra_raw = extra_path.read_bytes()
                        assert not extra_raw.startswith(b'\xef\xbb\xbf')
                        assert json.loads(extra_raw) == data['result_extra_json']

                    def analyze(name, expected_status=200):
                        page.locator('#url').fill(f'{base}/fixtures/{name}')
                        with page.expect_response(lambda response: response.url == base + '/api/analyze') as pending:
                            page.locator('#analyze').click()
                        response = pending.value
                        assert response.status == expected_status, response.text()
                        page.wait_for_function("!document.querySelector('#analyze').disabled")
                        data = response.json()
                        if expected_status == 200:
                            assert json.loads(main.result_path.with_name('result_extra.json').read_bytes()) == data['result_extra_json']
                        return data

                    data = analyze('root')
                    assert len(data['findings']) == 9, data
                    assert data['result_json']['findings'] == []
                    assert all(item['submission_status'] == 'needs_review' for item in data['findings'])
                    assert data['warnings'] and '일부 범위 미분석' in page.locator('#status').inner_text()
                    assert json.loads(main.result_path.read_text(encoding='utf-8')) == data['result_json']
                    download_json(data, 'static-partial')
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
                        summary = json.loads(page.locator('#output').text_content())
                        expected = [f for f in data['findings'] if technique == 'ALL' or f['technique'] == technique]
                        assert summary['totalFindings'] == len(expected)
                        assert all(f['evidence'] for f in summary['findings'])
                    page.locator('#techniqueFilter').select_option('JAMO')
                    assert json.loads(page.locator('#output').text_content())['totalFindings'] == 1
                    download_json(data, 'filtered-full')
                    # Another client may replace the shared server file; this page retains its own result.
                    other = page.request.post(base + '/api/analyze', data={'url': base + '/fixtures/clean'})
                    assert other.status == 200
                    assert json.loads(main.result_path.read_text(encoding='utf-8'))['findings'] == []
                    download_json(data, 'retained-result')
                    previous = main.result_path.read_bytes()
                    analyze('missing', 502)
                    assert page.locator('#status').inner_text() == '오류 발생'
                    assert page.locator('#download').is_disabled()
                    assert main.result_path.read_bytes() == previous
                    page.locator('#techniqueFilter').select_option('ALL')
                    assert '수집하지 못했습니다' in page.locator('#output').text_content()
                    clean = analyze('clean')
                    assert clean['findings'] == [] and not clean['warnings']
                    assert '위장·은닉 0개, 광고 후보 0개' in page.locator('#status').inner_text()
                    download_json(clean, 'static-empty')
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
                    assert json.loads(page.locator('#output').text_content())['collectionMode'] == 'browser'
                    download_json(runtime, 'dynamic-full')
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
                    download_json(partial, 'dynamic-partial')
                    previous = main.result_path.read_bytes()
                    analyze('missing', 502)
                    assert page.locator('#download').is_disabled()
                    assert main.result_path.read_bytes() == previous
                    clean = analyze('clean')
                    assert clean['findings'] == [] and clean['collection_mode'] == 'browser'
                    download_json(clean, 'dynamic-empty')
                    # Startup and waiting both share the analysis deadline.
                    previous = main.result_path.read_bytes()
                    expired = page.request.post(base + '/api/analyze', data={
                        'url': base + '/fixtures/dynamic', 'collection_mode': 'browser',
                        'total_timeout_sec': 0.1, 'render_wait_ms': 5000,
                    })
                    assert expired.status == 504, expired.text()
                    assert main.result_path.read_bytes() == previous
                    page.locator('#collectionMode').select_option('static')
                    content = analyze('content')
                    assert len(content['content_candidates']) == 2 and not content['findings']
                    assert len(content['result_extra_json']['findings']) == 2
                    assert all(item['technique'] == 'ETC' for item in content['result_extra_json']['findings'])
                    assert '광고 후보 2개' in page.locator('#status').inner_text()
                    assert {item['location'] for item in content['content_candidates']} == {'p#gamble', 'p#adult'}
                    for category in ['GAMBLING', 'ADULT_CONTENT']:
                        page.locator('#techniqueFilter').select_option(category)
                        summary = json.loads(page.locator('#output').text_content())
                        assert summary['totalContentCandidates'] == 1
                        assert summary['totalFindings'] == 0
                    with page.expect_download() as pending:
                        page.locator('#downloadContent').click()
                    download = pending.value
                    assert download.suggested_filename == 'content-candidates.json'
                    path = Path(temporary) / 'content-candidates.json'
                    download.save_as(path)
                    report = json.loads(path.read_text(encoding='utf-8'))
                    assert report['candidates'] == content['content_candidates']
                    assert report['purpose'] == 'content_candidate_review'
                    assert report['policy_version'] == content['content_policy_version'] == 'content-rules-v4'
                    download_json(content, 'content-four-technique-json')
                    analyze('missing', 502)
                    assert page.locator('#downloadContent').is_disabled()
                    assert page.locator('#downloadExtra').is_disabled()
                    assert not errors, errors
                    static_computed = analyze('computed')
                    assert {(item['location'], item['technique']) for item in static_computed['findings']} == {
                        ('p#overridden', 'TRANSPARENT'), ('p#partial', 'OFFSCREEN'), ('p#stroke', 'TRANSPARENT')}
                    page.locator('#collectionMode').select_option('browser')
                    computed = analyze('computed')
                    expected = {
                        ('p#' + name, technique) for name, technique in [
                            ('opacity', 'TRANSPARENT'), ('same', 'TRANSPARENT'),
                            ('display-child', 'OFFSCREEN'), ('tiny-child', 'OFFSCREEN'),
                            ('outside', 'OFFSCREEN'), ('alpha', 'TRANSPARENT'),
                            ('hidden-child', 'TRANSPARENT'), ('external', 'TRANSPARENT')]
                    } | {('iframe#styled-frame >>> p#frame-style', 'TRANSPARENT')}
                    styled_target = browser.new_page()
                    styled_target.goto(base + '/fixtures/computed')

                    def resolved_ids(location):
                        context = styled_target.main_frame
                        identities = []
                        segments = location.split(' >>> ')
                        for index, selector in enumerate(segments):
                            element = context.locator(selector)
                            assert element.count() == 1, location
                            identities.append(element.get_attribute('id'))
                            if index < len(segments) - 1:
                                context = element.element_handle().content_frame()
                        return tuple(identities)

                    actual = {(resolved_ids(item['location']), item['technique']) for item in computed['findings']}
                    expected_ids = {(resolved_ids(location), technique) for location, technique in expected}
                    assert actual == expected_ids and len(computed['findings']) == len(expected), (actual, expected_ids)
                    styled_target.close()
                    assert computed['content_candidates'][0]['techniques'] == ['TRANSPARENT']
                    download_json(computed, 'computed-styles')
                    # Save styles with HTML and replay offline using independently specified labels.
                    capture_dir = Path(temporary) / 'computed-capture'
                    captured = subprocess.run(
                        [sys.executable, '-B', 'scripts/validate_site.py', 'capture',
                         base + '/fixtures/computed', '--output', str(capture_dir), '--mode', 'browser'],
                        cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True,
                        timeout=30, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
                    )
                    assert captured.returncode == 0, captured.stderr
                    labels_path = capture_dir / 'labels.json'
                    labels = json.loads(labels_path.read_bytes())
                    labels.update(complete=True, policy='Synthetic computed-style features only, not ad verdicts')
                    labels['labels'] = [dict(url=base + '/fixtures/computed', location=location,
                                             technique=technique, expected=True, reviewed=True,
                                             reason='Independent synthetic fixture expectation')
                                        for location, technique in sorted(expected)]
                    labels['labels'].extend(dict(url=base + '/fixtures/computed', location='#' + name,
                                                  technique=technique, expected=False, reviewed=True,
                                                  reason='Synthetic fixture remains visible')
                                             for name, technique in [('overridden', 'TRANSPARENT'),
                                                ('partial', 'OFFSCREEN'), ('below', 'OFFSCREEN'),
                                                ('shadow', 'TRANSPARENT'), ('stroke', 'TRANSPARENT')])
                    labels_path.write_text(json.dumps(labels), encoding='utf-8')
                    replay = evaluate_capture(capture_dir)
                    assert replay['counts'] == dict(tp=9, fp=0, fn=0, tn=5), replay
                    assert replay['metrics']['recall'] == 1
                    assert replay['submission_candidate_count'] == 1
                    page.locator('#techniqueFilter').select_option('ALL')
                    policy = analyze('policy')
                    assert len(policy['findings']) == 7, policy
                    assert {item['technique'] for item in policy['result_json']['findings']} == {
                        'HOMOGLYPH', 'JAMO', 'TRANSPARENT', 'OFFSCREEN'}
                    assert len(policy['result_json']['findings']) == 4
                    assert sum(item['submission_status'] == 'needs_review' for item in policy['findings']) == 3
                    assert not any('policy-chat' in item['location'] for item in policy['findings'])
                    assert page.locator('#findingCards article').count() == 7
                    assert page.locator('#findingCards .included').count() == 4
                    assert page.locator('#findingCards .review').count() == 3
                    assert page.locator('#rawDetails').get_attribute('open') is None
                    assert not page.locator('#output').is_visible()
                    assert 'confidence' not in policy['findings'][0]
                    assert 'ㅋㅏㅈㅣㄴㅗ' in page.locator('#findingCards').inner_text()
                    assert '<img src=x' in page.locator('#findingCards').inner_text()
                    assert page.locator('#findingCards img').count() == 0
                    assert page.evaluate('window.__injected !== true')
                    assert any('ㅋㅏㅈㅣㄴㅗ' in item['evidence_text'] for item in policy['result_json']['findings'])
                    policy_summary = json.loads(page.locator('#output').text_content())
                    assert policy_summary['totalSubmittedFindings'] == 4
                    assert policy_summary['totalNeedsReviewFindings'] == 3
                    page.set_viewport_size({'width': 390, 'height': 844})
                    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
                    page.set_viewport_size({'width': 1100, 'height': 950})
                    screenshot = Path(__file__).resolve().parents[1] / '.validation' / 'result-cards-20261025.png'
                    screenshot.parent.mkdir(exist_ok=True)
                    page.screenshot(path=str(screenshot), full_page=True)
                    download_json(policy, 'policy-selected')
                    print(f'Browser checks passed: Edge {browser.version}; UI, filters, partial results, failure recovery, empty results')
                    print('Dynamic checks passed: static=0/browser=11; fetched comments, runtime links/depth, live repeated/nested frames, scripted srcdoc/about:blank, locations, file, JS/frame failure warnings, 502/504 preservation')
                    print('Download checks passed: filename, UTF-8 without BOM, full/filtered/partial/empty/static/dynamic results, per-page retention, failure disabled')
                    print('Content checks passed: promotion candidates, education exclusion, category filters, separate full download, original result schema')
                    print('Computed styles passed: classes, external CSS, solid background, inherited hiding/font, negative geometry, visible overrides/shadow/stroke, styled iframe, saved offline replay')
                    print('Submission policy passed: 4 attributed promotions, 3 review findings, laughter excluded, readable cards, collapsed JSON, original evidence/downloads')
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            sock.close()
            main.result_path = original_result_path
            if thread.is_alive():
                raise RuntimeError('Local test server did not stop')


if __name__ == '__main__':
    run()
