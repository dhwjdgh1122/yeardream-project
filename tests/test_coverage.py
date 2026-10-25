from fastapi.testclient import TestClient

from backend.app import crawler, main
from backend.app.coverage import build_coverage
from backend.app.limits import AnalysisTimeout


def test_main_entry_reports_known_board_not_visited_at_eight_contexts(monkeypatch, tmp_path):
    root = 'https://example.com/'
    html = ''.join(f'<a href="/about-{i}">About</a>' for i in range(7)) + '<a href="/board">Board</a>'
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kw: (html if url == root else '<p>About</p>', url))
    monkeypatch.setattr(main, 'result_path', tmp_path / 'result.json')
    with TestClient(main.app) as client:
        response = client.post('/api/analyze', json={'url': root})
    assert response.status_code == 200
    data = response.json()
    c = data['coverage']
    assert c['analyzed_documents'] == c['collected_documents'] == c['attempted_documents'] == 8
    assert c['website_complete'] is False
    assert c['unvisited_links'] == [dict(url=root + 'board', source_url=root, reason='max_pages')]
    assert c['limits']['max_documents'] == 8
    assert c['stop_reasons'] == ['max_pages']
    assert len(data['result_json']['findings']) == 0


def test_collected_and_analyzed_are_distinct_when_detection_times_out(monkeypatch, tmp_path):
    pages = [dict(url='https://example.com/', html='<p>OK</p>'),
             dict(url='https://example.com/next', html='<p>Next</p>'),
             dict(url='https://example.com/failed', error='HTTP 404')]
    monkeypatch.setattr(main, 'crawl_site', lambda *a, **kw: pages)
    def detect(page, **kw):
        if page is pages[1]:
            raise AnalysisTimeout()
        return []
    monkeypatch.setattr(main, 'detect_page', detect)
    monkeypatch.setattr(main, 'result_path', tmp_path / 'result.json')
    with TestClient(main.app) as client:
        data = client.post('/api/analyze', json={'url': pages[0]['url']}).json()
    assert data['coverage']['collected_documents'] == 2
    assert data['coverage']['analyzed_documents'] == data['coverage']['failed_documents'] == 1
    assert [d['status'] for d in data['coverage']['documents']] == [
        'analyzed', 'not_analyzed', 'collection_failed']


def test_redirects_depth_limits_and_frames_keep_distinct_meanings():
    root = dict(url='https://example.com/new', requested_url='https://example.com/old',
                links=['https://example.com/old', 'https://example.com/deep'],
                link_omissions=[dict(url='https://example.com/deep', reason='max_depth')],
                frame_omissions=[dict(location='iframe#external', reason='unsupported_or_external_src')],
                pending_contexts=[dict(url='https://example.com/frame', frame_path=['iframe#queued'],
                                       parent_url='https://example.com/new')],
                crawl_stop_reason='max_pages')
    iframe = dict(url='https://example.com/new', frame_path=['iframe#inline'])
    c = build_coverage([root, iframe], [root, iframe], max_pages=2, max_depth=0, timeout_sec=60)
    assert c['unvisited_links'] == [dict(url='https://example.com/deep',
        source_url=root['url'], reason='max_depth')]
    assert c['analyzed_documents'] == 2  # Same URL, separate iframe context.
    assert [x['reason'] for x in c['excluded_frames']] == ['unsupported_or_external_src', 'max_pages']
    assert c['website_complete'] is False


def test_empty_pending_queue_does_not_mean_whole_website_complete():
    page = dict(url='https://example.com/')
    c = build_coverage([page], [page], max_pages=8, max_depth=2, timeout_sec=60)
    assert c['unvisited_known_urls'] == 0
    assert c['website_complete'] is False


def test_crawler_pending_frame_is_recorded_at_document_limit(monkeypatch):
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kw: ('<iframe src="/frame"></iframe>', url))
    pages = crawler.crawl_site('https://example.com/', max_pages=1)
    assert pages[0]['pending_contexts'][0]['frame_path'] == ['iframe']
    c = build_coverage(pages, pages, max_pages=1, max_depth=2, timeout_sec=60)
    assert c['excluded_frames'][0]['reason'] == 'max_pages'


def test_interrupted_request_is_not_reported_as_an_unvisited_link(monkeypatch):
    from backend.app import limits
    clock = [0.0]
    monkeypatch.setattr(limits, 'monotonic', lambda: clock[0])
    def fetch(url, **kw):
        if url.endswith('/slow'):
            clock[0] = 2.0
        return '<a href="/slow">Slow</a><a href="/later">Later</a>', url
    monkeypatch.setattr(crawler, 'fetch_html', fetch)
    pages = crawler.crawl_site('https://example.com', total_timeout_sec=1)
    c = build_coverage(pages, pages, max_pages=8, max_depth=2, timeout_sec=1)
    assert c['attempted_documents'] == 2
    assert c['failed_documents'] == 1
    assert c['documents'][-1]['url'] == 'https://example.com/slow'
    assert [u['url'] for u in c['unvisited_links']] == ['https://example.com/later']
