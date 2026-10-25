import httpx
import pytest
from fastapi.testclient import TestClient

from backend.app import crawler, limits, main
from backend.app.detection import detect_page
from backend.app.content import detect_content


@pytest.fixture
def clock(monkeypatch):
    now = [0.0]
    monkeypatch.setattr(limits, 'monotonic', lambda: now[0])
    return now


def test_link_depth_boundary_and_iframe_depth_are_independent(monkeypatch):
    documents = {
        'https://example.com': '<a href="/child">Child</a><iframe src="/frame"></iframe>',
        'https://example.com/frame': '<a href="/from-frame">Link</a><p>Frame</p>',
        'https://example.com/child': '<a href="/deep">Deep</a>',
        'https://example.com/from-frame': '<p>Linked from frame</p>',
    }
    called = []

    def fetch(url, **kwargs):
        called.append(url)
        return documents[url], url

    monkeypatch.setattr(crawler, 'fetch_html', fetch)
    pages = crawler.crawl_site('https://example.com', max_depth=0)
    assert called == ['https://example.com', 'https://example.com/frame']
    assert all(page['depth'] == 0 for page in pages)
    assert all(page['link_omissions'] for page in pages)
    called.clear()
    pages = crawler.crawl_site('https://example.com', max_depth=1)
    assert set(called) == set(documents)
    child = next(page for page in pages if page['url'].endswith('/child'))
    assert child['depth'] == 1
    assert child['link_omissions'] == [{'url': 'https://example.com/deep', 'reason': 'max_depth'}]


def test_expired_budget_prevents_first_request(monkeypatch, clock):
    def unexpected_fetch(*args, **kwargs):
        pytest.fail('Expired budget must not make an HTTP request')

    monkeypatch.setattr(crawler, 'fetch_html', unexpected_fetch)
    pages = crawler.crawl_site('https://example.com', deadline=limits.Deadline(0))
    assert len(pages) == 1
    assert pages[0]['crawl_stop_reason'] == 'total_timeout'


def test_slow_fetch_stops_before_next_url(monkeypatch, clock):
    called = []

    def fetch(url, **kwargs):
        called.append(url)
        if url.endswith('/slow'):
            clock[0] = 2
        return '<a href="/slow">Slow</a><a href="/later">Later</a>', url

    monkeypatch.setattr(crawler, 'fetch_html', fetch)
    pages = crawler.crawl_site('https://example.com', total_timeout_sec=1)
    assert called == ['https://example.com', 'https://example.com/slow']
    assert len(pages) == 1
    assert pages[-1]['crawl_stop_reason'] == 'total_timeout'


def test_http_timeout_uses_remaining_budget_and_preserves_text(monkeypatch, clock):
    client_class = httpx.Client

    def respond(request):
        assert all(value == 0.5 for value in request.extensions['timeout'].values())
        return httpx.Response(200, content='정상'.encode('utf-8'), headers={'content-type': 'text/html; charset=utf-8'})

    transport = httpx.MockTransport(respond)
    monkeypatch.setattr(crawler.httpx, 'Client', lambda **kwargs: client_class(transport=transport, **kwargs))
    text, url = crawler.fetch_html('https://example.com', deadline=limits.Deadline(0.5))
    assert text == '정상'
    assert url == 'https://example.com'


def test_streaming_response_checks_absolute_deadline(monkeypatch, clock):
    class SlowStream(httpx.SyncByteStream):
        def __iter__(self):
            yield b'first'
            clock[0] = 2
            yield b'late'

    client_class = httpx.Client
    transport = httpx.MockTransport(lambda request: httpx.Response(200, stream=SlowStream()))
    monkeypatch.setattr(crawler.httpx, 'Client', lambda **kwargs: client_class(transport=transport, **kwargs))
    with pytest.raises(limits.AnalysisTimeout):
        crawler.fetch_html('https://example.com', deadline=limits.Deadline(1))


def test_timeout_before_detection_returns_504_without_overwriting(monkeypatch, tmp_path, clock):
    def fetch(url, **kwargs):
        clock[0] = 2
        return '<p>Late</p>', url

    monkeypatch.setattr(crawler, 'fetch_html', fetch)
    output = tmp_path / 'result.json'
    output.write_text('previous', encoding='utf-8')
    monkeypatch.setattr(main, 'result_path', output)
    with TestClient(main.app) as client:
        response = client.post('/api/analyze', json={'url': 'https://example.com', 'total_timeout_sec': 1})
    assert response.status_code == 504
    assert output.read_text(encoding='utf-8') == 'previous'


def test_timeout_after_completed_page_returns_partial_findings(monkeypatch, tmp_path, clock):
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kwargs: (
        '<p id="ad" style="opacity:0">Ad</p><a href="/child">Child</a>' if url.endswith('.com') else '<p>Child</p>', url))

    def detect(page, **kwargs):
        findings = detect_content(page, **kwargs)
        clock[0] = 2
        return findings

    monkeypatch.setattr(main, 'detect_content', detect)
    monkeypatch.setattr(main, 'result_path', tmp_path / 'result.json')
    with TestClient(main.app) as client:
        response = client.post('/api/analyze', json={'url': 'https://example.com', 'total_timeout_sec': 1})
    assert response.status_code == 200
    assert len(response.json()['findings']) == 1
    assert response.json()['warnings']


def test_depth_limit_is_reported_by_api(monkeypatch, tmp_path):
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kwargs: ('<a href="/child">Child</a>', url))
    monkeypatch.setattr(main, 'result_path', tmp_path / 'result.json')
    with TestClient(main.app) as client:
        response = client.post('/api/analyze', json={'url': 'https://example.com', 'max_depth': 0})
    assert response.status_code == 200
    assert len(response.json()['crawled_pages']) == 1
    assert any('max_depth=0' in warning for warning in response.json()['warnings'])


@pytest.mark.parametrize('options', [{'max_depth': -1}, {'max_depth': 21}, {'total_timeout_sec': 0}, {'total_timeout_sec': 1801}])
def test_invalid_limit_options_are_rejected(options):
    with TestClient(main.app) as client:
        response = client.post('/api/analyze', json={'url': 'https://example.com', **options})
    assert response.status_code == 422


@pytest.mark.parametrize('seconds', [float('nan'), float('inf'), 0, -1])
def test_nonfinite_or_nonpositive_budget_is_rejected(seconds):
    with pytest.raises(ValueError):
        limits.Deadline.after(seconds)
