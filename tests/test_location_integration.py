import json
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from fastapi.testclient import TestClient

from backend.app import crawler, main


def test_locations_survive_crawl_api_result_and_file(monkeypatch, tmp_path):
    documents = {
        'https://example.com': '''<title>Root</title>
            <p class="ad" style="opacity:0">First</p>
            <p class="ad" style="opacity:0">Second</p>
            <iframe src="/shared"></iframe><iframe src="/shared"></iframe>
            <iframe src="/bad"></iframe>''',
        'https://example.com/shared': '<iframe id="inner" src="/nested"></iframe>',
        'https://example.com/nested': '<p id="ad:1" style="opacity:0">Nested</p>',
    }

    def fetch(url, **kwargs):
        if url.endswith('/bad'):
            raise RuntimeError('fixture failure')
        return documents[url], url

    monkeypatch.setattr(crawler, 'fetch_html', fetch)
    output = tmp_path / 'result.json'
    monkeypatch.setattr(main, 'result_path', output)
    with TestClient(main.app) as client:
        response = client.post('/api/analyze', json={'url': 'https://example.com'})
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data['warnings']) == 1
    assert 'https://example.com/bad' in data['warnings'][0]
    assert 'https://example.com/bad' not in data['crawled_pages']
    assert len(data['findings']) == 4
    assert len(data['result_json']['findings']) == 4
    assert len({f['location'] for f in data['findings']}) == 4
    assert json.loads(output.read_text(encoding='utf-8')) == data['result_json']
    assert not output.read_bytes().startswith(b'\xef\xbb\xbf')
    for internal, exported in zip(data['findings'], data['result_json']['findings']):
        assert internal['location'] == exported['location']
        assert internal['url'] == exported['url'] == 'https://example.com'
        document_url = internal['url']
        segments = internal['location'].split(' >>> ')
        for selector in segments[:-1]:
            soup = BeautifulSoup(documents[document_url], 'html.parser')
            frames = soup.select(selector)
            assert len(frames) == 1
            document_url = urljoin(document_url, frames[0]['src'])
        soup = BeautifulSoup(documents[document_url], 'html.parser')
        matches = soup.select(segments[-1])
        assert len(matches) == 1
        assert matches[0].get_text(strip=True) in internal['evidence']


def test_total_crawl_failure_is_not_an_empty_success_or_file_overwrite(monkeypatch, tmp_path):
    def fetch(url, **kwargs):
        raise RuntimeError('fixture failure')

    monkeypatch.setattr(crawler, 'fetch_html', fetch)
    output = tmp_path / 'result.json'
    output.write_text('previous result', encoding='utf-8')
    monkeypatch.setattr(main, 'result_path', output)
    with TestClient(main.app) as client:
        response = client.post('/api/analyze', json={'url': 'https://example.com'})
    assert response.status_code == 502
    assert 'result_json' not in response.json()
    assert output.read_text(encoding='utf-8') == 'previous result'


def test_analysis_reports_crawl_limits(monkeypatch, tmp_path):
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kwargs: (
        ''.join(f'<iframe src="/frame{i}"></iframe>' for i in range(10)) if url.endswith('.com') else '<p>Clean</p>', url))
    monkeypatch.setattr(main, 'result_path', tmp_path / 'result.json')
    with TestClient(main.app) as client:
        response = client.post('/api/analyze', json={'url': 'https://example.com'})
    assert response.status_code == 200
    assert response.json()['warnings']
    assert response.json()['result_json']['findings'] == []
