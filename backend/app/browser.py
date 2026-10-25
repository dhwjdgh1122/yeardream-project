"""Optional, request-scoped Edge rendering; static analysis needs no Playwright."""

from pathlib import Path

from .limits import AnalysisTimeout, Deadline


class BrowserUnavailable(RuntimeError):
    pass


class BrowserRenderer:
    def __init__(self, deadline: Deadline, wait_ms: int = 500):
        self.deadline = deadline
        self.wait_ms = wait_ms
        self.playwright = None
        self.browser = None
        self.page = None
        self.statuses = {}
        self.errors = []

    def timeout_ms(self):
        return min(10_000, self.deadline.remaining() * 1000)

    def __enter__(self):
        self.deadline.check()
        try:
            from playwright.sync_api import sync_playwright

            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                channel='msedge', headless=True, timeout=self.timeout_ms(),
            )
            context = self.browser.new_context(accept_downloads=False, service_workers='block')
            self.page = context.new_page()
            self.page.on('response', self._record_response)
            self.page.on('pageerror', lambda error: self.errors.append(str(error)[:300]))
            self.page.on('popup', lambda popup: popup.close())
            self.deadline.check()
            return self
        except Exception as exc:
            self.__exit__(None, None, None)
            self.deadline.check()
            if isinstance(exc, AnalysisTimeout):
                raise
            raise BrowserUnavailable(
                '동적 분석을 시작하지 못했습니다. Playwright와 Microsoft Edge 설치 및 실행 환경을 확인해 주세요.'
            ) from exc

    def __exit__(self, *args):
        try:
            if self.browser is not None:
                self.browser.close()
        finally:
            if self.playwright is not None:
                self.playwright.stop()

    def _record_response(self, response):
        if response.request.is_navigation_request():
            self.statuses[response.frame] = response.status

    def fetch(self, url):
        self.statuses.clear()
        self.errors.clear()
        self.page.set_default_timeout(self.timeout_ms())
        self.page.goto(url, wait_until='domcontentloaded', timeout=self.timeout_ms())
        self.deadline.check()
        # A bounded observation window, not a promise of complete page loading.
        if self.wait_ms:
            self.page.wait_for_timeout(min(self.wait_ms, self.deadline.remaining() * 1000))
        self.deadline.check()
        return self.snapshot(self.page.main_frame, self.page.url)

    def snapshot(self, frame, url):
        self.deadline.check()
        if frame.is_detached():
            raise RuntimeError('렌더링 중 iframe이 제거되었습니다.')
        if self.statuses.get(frame, 200) >= 400:
            raise RuntimeError(f'브라우저 문서 HTTP {self.statuses[frame]}')
        snapshot = frame.evaluate(Path(__file__).with_name('rendered_snapshot.js').read_text(encoding='utf-8'),
                                  self.deadline.remaining() * 1000)
        self.deadline.check()
        current_url = frame.url
        if current_url not in {'about:blank', 'about:srcdoc'}:
            url = current_url
        return {
            **snapshot, 'url': url, 'browser_frame': frame,
            'collection_warnings': [f'페이지 JavaScript 오류: {error}' for error in self.errors],
        }

    def child_frame(self, parent, selector):
        self.deadline.check()
        element = parent.query_selector(selector)
        return element.content_frame() if element else None

    def frame_url(self, frame):
        return frame.url
