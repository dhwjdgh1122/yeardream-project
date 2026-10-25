"""Check only history/review flows in installed Edge, using isolated local fixtures."""

import json
import socket
import sys
import tempfile
import threading
import time
from pathlib import Path

import uvicorn
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app import main


def run():
    original = main.result_path, main.history_path, main.crawl_site
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    base = f'http://127.0.0.1:{sock.getsockname()[1]}'
    server = uvicorn.Server(uvicorn.Config(main.app, log_level='error'))
    thread = threading.Thread(target=server.run, kwargs={'sockets': [sock]}, daemon=True)
    with tempfile.TemporaryDirectory(prefix='yeardream-history-') as temporary:
        main.result_path = Path(temporary) / 'result.json'
        main.history_path = Path(temporary) / 'history.sqlite3'
        main.crawl_site = lambda url, **kw: [{'url': url, 'html': '''
            <p style="opacity:0">카지노 가입 보너스 &lt;img src=x onerror=alert(1)&gt;</p>'''}]
        try:
            thread.start()
            limit = time.monotonic() + 10
            while not server.started:
                if not thread.is_alive() or time.monotonic() > limit:
                    raise RuntimeError('History test server failed to start')
                time.sleep(.05)
            with sync_playwright() as playwright:
                with playwright.chromium.launch(channel='msedge', headless=True) as browser:
                    page = browser.new_page(viewport={'width': 390, 'height': 844})
                    errors = []
                    page.on('pageerror', lambda error: errors.append(str(error)))
                    page.goto(base + '/history')
                    page.wait_for_function("document.querySelector('#message').textContent.includes('저장된 분석이 없습니다')")
                    response = page.request.post(base + '/api/analyze', data={'url': 'https://example.com'})
                    assert response.status == 200
                    analysis = response.json()
                    official = main.result_path.read_bytes()
                    page.get_by_role('button', name='이력 새로고침').click()
                    page.get_by_role('button', name='https://example.com', exact=True).click()
                    page.locator('#detail form').first.wait_for()
                    assert page.locator('#detail img').count() == 0
                    form = page.locator('#detail form').first
                    form.get_by_label('검토 결과').select_option('uncertain')
                    form.get_by_label('검토자').fill('<img src=x onerror=alert(1)>')
                    form.get_by_label('판단 이유').fill('추가 문맥 확인 필요')
                    form.get_by_role('button', name='검토 기록 추가').click()
                    page.get_by_text('저장했습니다. 기존 분석·제출 결과는 유지됩니다.').wait_for()
                    assert page.locator('#detail img').count() == 0
                    page.reload()
                    page.get_by_role('button', name='https://example.com', exact=True).click()
                    page.get_by_text('추가 문맥 확인 필요', exact=False).wait_for()
                    assert main.result_path.read_bytes() == official
                    assert page.request.get(base + '/api/history/' + analysis['analysis_id']).json()['candidates'][0]['reviews'][0]['decision'] == 'uncertain'
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                    main.history_path = Path(temporary)
                    page.get_by_role('button', name='이력 새로고침').click()
                    page.get_by_text('이력 저장소를 사용할 수 없습니다.', exact=True).wait_for()
                    assert not errors, errors
                    print(json.dumps({'status': 'passed', 'edge': browser.version,
                                      'checks': ['empty history', 'saved analysis', 'review persistence',
                                                 'literal HTML safety', '390px layout',
                                                 'official JSON preserved', 'database failure']}))
        finally:
            server.should_exit = True
            thread.join(timeout=10)
            sock.close()
            main.result_path, main.history_path, main.crawl_site = original
            if thread.is_alive():
                raise RuntimeError('History test server did not stop')


if __name__ == '__main__':
    run()
