import json
from pathlib import Path

from fastapi.testclient import TestClient

from backend.app import crawler, main


def test_health_and_frontend_are_served():
    with TestClient(main.app) as client:
        assert client.get('/api/health').json() == {'status': 'ok'}
        response = client.get('/')
        assert response.status_code == 200
        assert '<html lang="ko">' in response.text
    root = Path(__file__).resolve().parents[1]
    assert main.result_path == root / 'result.json'


def test_analyze_collects_linked_pages_and_saves_matching_result(monkeypatch, tmp_path):
    pages = {
        'https://example.com': '<title>Fixture</title><a href="/child">Child</a>',
        'https://example.com/child': '<div id="promo" style="color:transparent">광고</div>',
    }
    requested = []

    def fetch(url, **kwargs):
        requested.append(url)
        return pages[url], url

    monkeypatch.setattr(crawler, 'fetch_html', fetch)
    output = tmp_path / 'result.json'
    monkeypatch.setattr(main, 'result_path', output)
    with TestClient(main.app) as client:
        response = client.post('/api/analyze', json={'url': 'https://example.com'})

    assert response.status_code == 200, response.text
    data = response.json()
    assert requested == list(pages)
    assert data['crawled_pages'] == list(pages)
    assert data['page_title'] == 'Fixture'
    assert len(data['findings']) == 1
    finding = data['result_json']['findings'][0]
    assert finding['technique'] == 'TRANSPARENT'
    assert finding['evidence_text'] == data['findings'][0]['evidence']
    assert finding['location'] == data['findings'][0]['location']
    raw = output.read_bytes()
    assert not raw.startswith(b'\xef\xbb\xbf')
    assert '광고' in raw.decode('utf-8') or '은닉' in raw.decode('utf-8')
    assert json.loads(raw) == data['result_json']


def test_analyze_clean_page_returns_empty_findings(monkeypatch, tmp_path):
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kwargs: ('<p>Clean</p>', url))
    monkeypatch.setattr(main, 'result_path', tmp_path / 'result.json')
    with TestClient(main.app) as client:
        response = client.post('/api/analyze', json={'url': 'https://example.com'})
    assert response.status_code == 200
    assert response.json()['result_json']['findings'] == []
