"""Exercise live progress, reload/reconnect and partial cancellation in real Edge."""

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
from backend.app import crawler, main


def run():
    original = main.result_path, main.history_path, crawler.fetch_html
    blocked = threading.Event()
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    base = f'http://127.0.0.1:{sock.getsockname()[1]}'
    server = uvicorn.Server(uvicorn.Config(main.app, log_level='error'))
    thread = threading.Thread(target=server.run, kwargs={'sockets': [sock]}, daemon=True)
    calls = []
    def fetch(url, **kw):
        calls.append(url)
        if '/xboard/' in url or url.endswith('/empty'):
            blocked.set()
            kw['deadline'].cancel_event.wait(10)
            kw['deadline'].check()
        return ('<p style="opacity:0">카지노 가입 보너스</p>' +
                ''.join(f'<a href="/about{i}">About</a>' for i in range(20)) +
                '<a href="/xboard/board.php?tbnum=6">자유게시판</a>'), url
    with tempfile.TemporaryDirectory(prefix='yeardream-jobs-') as temporary:
        main.result_path = Path(temporary) / 'result.json'
        main.history_path = Path(temporary) / 'history.sqlite3'
        crawler.fetch_html = fetch
        try:
            thread.start()
            limit = time.monotonic() + 10
            while not server.started:
                if not thread.is_alive() or time.monotonic() >= limit:
                    raise RuntimeError('Local job test server did not start')
                time.sleep(.05)
            with sync_playwright() as playwright:
                with playwright.chromium.launch(channel='msedge', headless=True) as browser:
                    page = browser.new_page(viewport={'width': 390, 'height': 844})
                    errors = []
                    page.on('pageerror', lambda error: errors.append(str(error)))
                    page.goto(base)
                    assert page.locator('#maxPages').input_value() == '100'
                    assert page.locator('#maxDepth').input_value() == '4'
                    assert page.locator('#timeBudget').input_value() == '25'
                    page.locator('#url').fill('https://fixture.example/')
                    page.locator('#analyze').click()
                    assert blocked.wait(3)
                    page.wait_for_function("document.querySelector('#jobStatus').textContent.includes('탐지 완료 1문서')")
                    assert page.locator('#jobProgress').get_attribute('value') is None
                    assert calls[1] == 'https://fixture.example/xboard/board.php?tbnum=6'
                    screenshot = Path(__file__).resolve().parents[1] / '.validation' / 'job-progress-20261025.png'
                    screenshot.parent.mkdir(exist_ok=True)
                    page.screenshot(path=str(screenshot), full_page=True)
                    page.reload()
                    assert page.locator('#analyze').inner_text() == '진행 확인 재시도'
                    page.locator('#analyze').click()
                    page.wait_for_function("document.querySelector('#jobStatus').textContent.includes('탐지 완료 1문서')")
                    page.locator('#cancelJob').click()
                    page.wait_for_function("!document.querySelector('#analyze').disabled")
                    assert '사용자 중단' in page.locator('#status').inner_text()
                    assert page.locator('#findingCards article').count() == 1
                    assert not page.locator('#download').is_disabled()
                    assert len(calls) == 2  # Reload resumes polling, not another scan.
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                    before = main.result_path.read_bytes()
                    blocked.clear()
                    page.locator('#url').fill('https://fixture.example/empty')
                    page.locator('#analyze').click()
                    assert blocked.wait(3)
                    page.locator('#cancelJob').click()
                    page.wait_for_function("!document.querySelector('#analyze').disabled")
                    assert page.locator('#status').inner_text() == '사용자 중단'
                    assert page.locator('#download').is_disabled()
                    assert main.result_path.read_bytes() == before
                    assert not errors, errors
                    print(json.dumps({'status': 'passed', 'edge': browser.version,
                        'checks': ['live counts', 'indeterminate progress', '100/4/25 defaults',
                                   'board priority', 'reload/reconnect without duplicate scan',
                                   'partial cancel', 'empty cancel preserves results', '390px layout']}))
        finally:
            for job_id, job in list(main.jobs.jobs.items()):
                if job['status'] not in {'completed', 'cancelled', 'failed'}:
                    main.jobs.cancel(job_id)
            server.should_exit = True
            thread.join(timeout=10)
            sock.close()
            main.result_path, main.history_path, crawler.fetch_html = original
            if thread.is_alive():
                raise RuntimeError('Job test server did not stop')


if __name__ == '__main__':
    run()
