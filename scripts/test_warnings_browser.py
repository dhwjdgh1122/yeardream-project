"""Check grouped notices in installed Edge without contacting public websites."""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright


def run():
    root = Path(__file__).resolve().parents[1]
    html = (root / 'frontend/static/index.html').read_text(encoding='utf-8')
    with sync_playwright() as playwright:
        with playwright.chromium.launch(channel='msedge', headless=True) as browser:
            page = browser.new_page(viewport={'width': 390, 'height': 844})
            errors = []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.route('http://warning-test.invalid/**', lambda route: route.fulfill(
                status=200, content_type='text/html; charset=utf-8', body=html))
            page.goto('http://warning-test.invalid/')
            page.evaluate('''() => {
                const notices = Array.from({length: 500}, (_, i) =>
                    'HTML 수집 대상이 아닌 첨부 링크 제외: https://example.com/?id=' + i + '&q=' + 'x'.repeat(500));
                notices.push('수집 실패: <img src=x onerror=alert(1)>',
                    '탐색이 중단돼 미분석 범위가 있습니다: max_pages',
                    'iframe 분석 제외: iframe (unsupported_or_external_src)');
                renderWarnings(notices);
            }''')
            groups = page.locator('#warnings details')
            assert groups.count() == 4
            assert page.locator('#warnings details[open]').count() == 0
            assert '503' in page.locator('#warnings > p').inner_text()
            assert '문서 수집 실패' in groups.nth(0).locator('summary').inner_text()
            attachments = groups.nth(2)
            assert '500' in attachments.locator('summary').inner_text()
            assert page.locator('#warnings img').count() == 0
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            attachments.locator('summary').click()
            assert attachments.get_attribute('open') is not None
            assert attachments.locator('li').count() == 500
            assert attachments.locator('ul').evaluate('(el) => el.scrollHeight > el.clientHeight')
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            folder = root / '.validation'
            folder.mkdir(exist_ok=True)
            page.screenshot(path=str(folder / 'warnings-grouped-mobile.png'), full_page=True)
            attachments.locator('summary').click()
            assert attachments.get_attribute('open') is None
            page.evaluate('renderWarnings([])')
            assert not page.locator('#warnings').is_visible()
            assert not errors, errors
            print(json.dumps({'status': 'passed', 'notices': 503, 'groups': 4,
                              'viewport': 390, 'browser': browser.version}))


if __name__ == '__main__':
    run()
