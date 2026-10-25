import pytest
from fastapi.testclient import TestClient

from backend.app import crawler, limits, main
from backend.app.detection import detect_page
from backend.app.browser import BrowserUnavailable


class RenderedDocuments:
    """A rendered tree whose identical-src frames contain different live text."""

    def __init__(self):
        self.opened = []
        self.documents = {
            'root': '<a href="/child">Child</a><iframe id="a" src="/shared"></iframe><iframe id="b" src="/shared"></iframe>',
            'a': '<p style="opacity:0">First runtime frame</p>',
            'b': '<p style="opacity:0">Second runtime frame</p>',
            'child': '<p style="opacity:0">Runtime child</p>',
        }

    def fetch(self, url):
        self.opened.append(url)
        key = 'child' if url.endswith('/child') else 'root'
        return self.snapshot(key, url + '#runtime')

    def snapshot(self, frame, url):
        return {'html': self.documents[frame], 'url': url, 'browser_frame': frame}

    def child_frame(self, parent, selector):
        return selector[-1]

    def frame_url(self, frame):
        return 'https://example.com/shared'


def test_browser_frames_preserve_live_insertion_context_and_link_depth():
    renderer = RenderedDocuments()
    pages = crawler.crawl_site('https://example.com', renderer=renderer, max_depth=0)
    assert renderer.opened == ['https://example.com']
    assert len(pages) == 3
    assert pages[0]['link_omissions']
    findings = [finding for page in pages for finding in detect_page(page)]
    assert len(findings) == 2
    assert len({finding['location'] for finding in findings}) == 2
    assert {'First runtime frame', 'Second runtime frame'} == {
        finding['evidence'].split('원문: ')[1] for finding in findings
    }
    assert all(finding['url'] == 'https://example.com' for finding in findings)
    renderer = RenderedDocuments()
    pages = crawler.crawl_site('https://example.com', renderer=renderer, max_depth=1)
    assert renderer.opened == ['https://example.com', 'https://example.com/child']
    assert len(pages) == 4
    assert pages[-1]['depth'] == 1


def test_rendered_frame_scope_depth_and_document_limits():
    renderer = RenderedDocuments()
    renderer.frame_url = lambda frame: 'https://outside.example/frame'
    pages = crawler.crawl_site('https://example.com', renderer=renderer, max_depth=0)
    assert len(pages) == 1
    assert len(pages[0]['frame_omissions']) == 2
    assert all(item['reason'] == 'unsupported_or_external_src' for item in pages[0]['frame_omissions'])
    pages = crawler.crawl_site('https://example.com', renderer=RenderedDocuments(), max_iframe_depth=0, max_depth=0)
    assert pages[0]['frame_omissions'][0]['reason'] == 'max_iframe_depth'
    pages = crawler.crawl_site('https://example.com', renderer=RenderedDocuments(), max_pages=1)
    assert len(pages) == 1 and pages[0]['crawl_truncated']


def test_browser_collection_obeys_shared_deadline(monkeypatch):
    clock = [0.0]
    monkeypatch.setattr(limits, 'monotonic', lambda: clock[0])
    renderer = RenderedDocuments()

    def late_fetch(url):
        clock[0] = 2.0
        return renderer.snapshot('root', url)

    renderer.fetch = late_fetch
    pages = crawler.crawl_site('https://example.com', renderer=renderer, total_timeout_sec=1)
    assert pages[0]['crawl_stop_reason'] == 'total_timeout'
    assert 'error' in pages[0]


def test_failed_live_frame_keeps_sibling_results():
    renderer = RenderedDocuments()
    snapshot = renderer.snapshot

    def fail_one(frame, url):
        if frame == 'b':
            raise RuntimeError('Frame detached during collection')
        return snapshot(frame, url)

    renderer.snapshot = fail_one
    pages = crawler.crawl_site('https://example.com', renderer=renderer, max_depth=0)
    assert len([page for page in pages if 'error' in page]) == 1
    assert len([finding for page in pages if 'error' not in page for finding in detect_page(page)]) == 1


def test_pending_and_removed_frames_are_explicit_omissions():
    renderer = RenderedDocuments()
    renderer.frame_url = lambda frame: 'about:blank'
    pages = crawler.crawl_site('https://example.com', renderer=renderer, max_depth=0)
    assert len(pages) == 1
    assert all(item['reason'] == 'frame_not_loaded' for item in pages[0]['frame_omissions'])
    renderer.child_frame = lambda *args: None
    pages = crawler.crawl_site('https://example.com', renderer=renderer, max_depth=0)
    assert all(item['reason'] == 'frame_unavailable' for item in pages[0]['frame_omissions'])


def test_live_frame_redirecting_outside_scope_is_not_analyzed():
    renderer = RenderedDocuments()
    snapshot = renderer.snapshot

    def redirected(frame, url):
        doc = snapshot(frame, url)
        if frame == 'b':
            doc['url'] = 'https://outside.example/frame'
        return doc

    renderer.snapshot = redirected
    pages = crawler.crawl_site('https://example.com', renderer=renderer, max_depth=0)
    assert len([page for page in pages if 'error' in page]) == 1
    findings = [finding for page in pages if 'error' not in page for finding in detect_page(page)]
    assert len(findings) == 1 and 'First runtime frame' in findings[0]['evidence']


@pytest.mark.parametrize('exception, status', [
    (BrowserUnavailable('Browser setup missing'), 503),
    (limits.AnalysisTimeout('Expired on startup'), 504),
])
def test_browser_startup_failure_preserves_previous_file(monkeypatch, tmp_path, exception, status):
    class Unavailable:
        def __enter__(self):
            raise exception

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(main, 'BrowserRenderer', lambda *args: Unavailable())
    output = tmp_path / 'result.json'
    output.write_text('previous', encoding='utf-8')
    monkeypatch.setattr(main, 'result_path', output)
    with TestClient(main.app) as client:
        response = client.post('/api/analyze', json={'url': 'https://example.com', 'collection_mode': 'browser'})
    assert response.status_code == status
    assert output.read_text(encoding='utf-8') == 'previous'


def test_browser_api_saves_runtime_results_and_closes_renderer(monkeypatch, tmp_path):
    closed = []

    class Renderer(RenderedDocuments):
        def __enter__(self):
            return self

        def __exit__(self, *args):
            closed.append(True)

    monkeypatch.setattr(main, 'BrowserRenderer', lambda *args: Renderer())
    monkeypatch.setattr(main, 'result_path', tmp_path / 'result.json')
    with TestClient(main.app) as client:
        response = client.post('/api/analyze', json={
            'url': 'https://example.com', 'collection_mode': 'browser', 'max_depth': 0,
        })
    assert response.status_code == 200, response.text
    assert response.json()['collection_mode'] == 'browser'
    assert len(response.json()['findings']) == 2
    assert closed == [True]
    assert main.result_path.exists()


@pytest.mark.parametrize('options', [
    {'collection_mode': 'invalid'}, {'render_wait_ms': -1}, {'render_wait_ms': 5001},
])
def test_invalid_render_options_are_rejected(options, monkeypatch):
    monkeypatch.setattr(crawler, 'fetch_html', lambda *args, **kwargs: pytest.fail('Invalid options must not fetch'))
    with TestClient(main.app) as client:
        response = client.post('/api/analyze', json={'url': 'https://example.com', **options})
    assert response.status_code == 422
