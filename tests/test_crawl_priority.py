from backend.app import crawler
from backend.app.coverage import build_coverage


def test_board_before_menu_and_posts_before_generic_pages(monkeypatch):
    root = 'https://example.com/'
    listing = root + 'xboard/board.php?tbnum=6'
    post = root + 'xboard/board.php?mode=view&number=107&tbnum=6'
    requests = []
    def fetch(url, **kw):
        requests.append(url)
        if url == root:
            return ''.join(f'<a href="/about{i}">About</a>' for i in range(20)) + '<a href="/xboard/board.php?tbnum=6"><img alt="자유게시판"></a>', url
        if url == listing:
            return '<a href="?mode=view&amp;number=107&amp;tbnum=6">Post</a>', url
        return '<p>Content</p>', url
    monkeypatch.setattr(crawler, 'fetch_html', fetch)
    pages = crawler.crawl_site(root, max_pages=3, prioritize_boards=True)
    assert requests == [root, listing, post]
    assert len(pages) == 3


def test_xboard_post_aliases_do_not_exhaust_budget(monkeypatch):
    root = 'https://example.com/'
    aliases = ['mode=view&number=107&tbnum=6&page=1',
               'tbnum=6&number=107&mode=view&page=2&searchword=&sCat=0',
               'mode=view&number=108&tbnum=6&page=1']
    calls = []
    def fetch(url, **kw):
        calls.append(url)
        return (''.join(f'<a href="/xboard/board.php?{q}">Post</a>' for q in aliases) if url == root else '<p>Post</p>'), url
    monkeypatch.setattr(crawler, 'fetch_html', fetch)
    pages = crawler.crawl_site(root, max_pages=10, prioritize_boards=True)
    assert len(calls) == 3
    coverage = build_coverage(pages, pages, max_pages=10, max_depth=2, timeout_sec=60, prioritize_boards=True)
    assert coverage['unvisited_known_urls'] == 0
    assert crawler.page_identity(root + '?q=one') != crawler.page_identity(root + '?q=two')


def test_incremental_callback_runs_before_next_request(monkeypatch):
    completed = []
    def fetch(url, **kw):
        if url.endswith('/child'):
            assert completed == ['https://example.com/']
        return ('<a href="/child">Child</a>' if url.endswith('.com/') else '<p>Child</p>'), url
    monkeypatch.setattr(crawler, 'fetch_html', fetch)
    crawler.crawl_site('https://example.com/', on_document=lambda page: completed.append(page['url']))
    assert completed == ['https://example.com/', 'https://example.com/child']


def test_attachments_are_not_fetched_and_relevant_board_children_are_promoted(monkeypatch):
    root = 'https://example.com/'
    first = root + 'board?tbnum=1'
    second = root + 'board?tbnum=2'
    calls = []
    def fetch(url, **kw):
        calls.append(url)
        if url == root:
            return '<a href="/board?tbnum=1">Board</a><a href="/board?tbnum=2">Board</a><a href="/large.pdf">PDF</a>', url
        if url == first:
            return '<a href="/board?tbnum=1&amp;mode=view&amp;number=107">Post</a><a href="/board?mode=downpost">File</a>', url
        return '<p>Post</p>', url
    monkeypatch.setattr(crawler, 'fetch_html', fetch)
    pages = crawler.crawl_site(root, max_pages=3, prioritize_boards=True,
                              on_document=lambda page: page['url'] == first)
    assert calls == [root, first, root + 'board?tbnum=1&mode=view&number=107']
    assert any(i['reason'] == 'attachment' for i in pages[0]['link_omissions'])


def test_xboard_go_links_use_explicit_read_view_without_merging_identity(monkeypatch):
    root = 'https://example.com/'
    go = root + 'xboard/board.php?mode=view&number=107&tbnum=6&mode1=go'
    read = root + 'xboard/board.php?mode=view&number=107&tbnum=6'
    calls = []
    def fetch(url, **kw):
        calls.append(url)
        assert url != go
        return (f'<a href="{go}">Read</a>' if url == root else '<p>Public post body</p>'), url
    monkeypatch.setattr(crawler, 'fetch_html', fetch)
    pages = crawler.crawl_site(root, prioritize_boards=True)
    assert calls == [root, read]
    assert pages[1]['source_link'] == go
    assert pages[0]['link_omissions'][0]['reason'] == 'redirect_link'
    assert crawler.page_identity(go) != crawler.page_identity(read)


def test_write_modify_delete_links_are_never_requested(monkeypatch):
    calls = []
    def fetch(url, **kw):
        calls.append(url)
        return '<a href="/board?mode=delete">Delete</a><a href="/board?mode=modify">Edit</a><a href="/board?mode=write">Write</a>', url
    monkeypatch.setattr(crawler, 'fetch_html', fetch)
    pages = crawler.crawl_site('https://example.com/', prioritize_boards=True)
    assert calls == ['https://example.com/']
    assert {x['reason'] for x in pages[0]['link_omissions']} == {'non_readonly'}


def test_shorter_path_can_expand_a_page_seen_first_via_deep_priority_path(monkeypatch):
    root = 'https://example.com/'
    docs = {root: '<a href="/board">Board</a><a href="/menu">Menu</a>',
        root+'board': '<a href="/board2">Board</a>',
        root+'board2': '<a href="/board-shared">Shared</a>',
        root+'board-shared': '<a href="/child">Child</a>',
        root+'menu': '<a href="/board-shared">Shared</a>', root+'child': '<p>Child</p>'}
    calls = []
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kw: (calls.append(url) or docs[url], url))
    pages = crawler.crawl_site(root, max_pages=20, max_depth=3, prioritize_boards=True)
    assert any(p['url']==root+'child' for p in pages)
    assert min(p['depth'] for p in pages if p['url']==root+'board-shared') == 2
