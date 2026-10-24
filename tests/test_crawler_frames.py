import html

from bs4 import BeautifulSoup

from backend.app import crawler
from backend.app.detection import detect_page


def test_nested_and_repeated_frames_keep_each_context(monkeypatch):
    documents = {
        'https://example.com': '<iframe src="/frame"></iframe><iframe src="/frame"></iframe>',
        'https://example.com/frame': '<iframe id="inner" src="nested"></iframe>',
        'https://example.com/nested': '<p id="ad" style="opacity:0">Ad</p>',
    }
    fetched = []

    def fetch(url, **kwargs):
        fetched.append(url)
        return documents[url], url

    monkeypatch.setattr(crawler, 'fetch_html', fetch)
    pages = crawler.crawl_site('https://example.com')
    findings = [finding for page in pages for finding in detect_page(page)]
    assert fetched == list(documents)
    assert len(pages) == 5
    assert {page['parent_url'] for page in pages if page['url'].endswith('/nested')} == {'https://example.com/frame'}
    assert len(findings) == 2
    assert {finding['url'] for finding in findings} == {'https://example.com'}
    assert len({finding['location'] for finding in findings}) == 2
    for finding in findings:
        document_url = finding['url']
        segments = finding['location'].split(' >>> ')
        for segment in segments[:-1]:
            soup = BeautifulSoup(documents[document_url], 'html.parser')
            frames = soup.select(segment)
            assert len(frames) == 1
            document_url = crawler.urljoin(document_url, frames[0]['src'])
        soup = BeautifulSoup(documents[document_url], 'html.parser')
        assert soup.select_one(segments[-1])['id'] == 'ad'


def test_frame_failure_does_not_stop_siblings_and_is_not_retried(monkeypatch):
    calls = []

    def fetch(url, **kwargs):
        calls.append(url)
        if url.endswith('/bad'):
            raise RuntimeError('fixture failure')
        if url.endswith('/good'):
            return '<p style="opacity:0">Ad</p>', url
        return '<iframe src="/bad"></iframe><iframe src="/bad"></iframe><iframe src="/good"></iframe>', url

    monkeypatch.setattr(crawler, 'fetch_html', fetch)
    pages = crawler.crawl_site('https://example.com')
    assert len([page for page in pages if 'error' in page]) == 2
    assert calls.count('https://example.com/bad') == 1
    assert any(detect_page(page) for page in pages if 'error' not in page)


def test_frame_depth_and_cycles_are_bounded(monkeypatch):
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kwargs: ('<iframe src="/next"></iframe>', url))
    pages = crawler.crawl_site('https://example.com', max_iframe_depth=0)
    assert len(pages) == 1
    assert pages[0]['frame_omissions'][0]['reason'] == 'max_iframe_depth'
    pages = crawler.crawl_site('https://example.com')
    assert len(pages) == 2
    assert pages[-1]['frame_omissions'][0]['reason'] == 'frame_cycle'


def test_srcdoc_and_external_frames_are_distinguished(monkeypatch):
    inner = html.escape('<p id="ad" style="opacity:0">Ad</p>', quote=True)
    markup = f'<iframe id="inline" srcdoc="{inner}"></iframe><iframe src="https://other.com"></iframe>'
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kwargs: (markup, url))
    pages = crawler.crawl_site('https://example.com')
    assert len(pages) == 2
    assert pages[0]['frame_omissions'][0]['reason'] == 'unsupported_or_external_src'
    finding = detect_page(pages[1])[0]
    assert finding['location'] == 'iframe#inline >>> p#ad'
    assert finding['url'] == 'https://example.com'


def test_context_limit_includes_failed_documents(monkeypatch):
    def fetch(url, **kwargs):
        if url.endswith('/bad'):
            raise RuntimeError('fixture failure')
        return '<a href="/bad">bad</a><a href="/other">other</a>', url
    monkeypatch.setattr(crawler, 'fetch_html', fetch)
    pages = crawler.crawl_site('https://example.com', max_pages=2)
    assert len(pages) == 2
    assert pages[-1]['error'] == 'fixture failure'
    assert pages[-1]['crawl_truncated'] is True


def test_fragment_links_do_not_rescan_the_same_page(monkeypatch):
    calls = []

    def fetch(url, **kwargs):
        calls.append(url)
        return '<a href="#one">One</a><a href="#two">Two</a><a href="mailto:a@example.com">Mail</a>', url

    monkeypatch.setattr(crawler, 'fetch_html', fetch)
    pages = crawler.crawl_site('https://example.com#start')
    assert len(pages) == 1
    assert calls == ['https://example.com']


def test_redirect_outside_scope_is_reported_as_failure(monkeypatch):
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kwargs: ('<p>External</p>', 'https://other.com'))
    pages = crawler.crawl_site('https://example.com')
    assert len(pages) == 1
    assert 'error' in pages[0]
    assert 'html' not in pages[0]
