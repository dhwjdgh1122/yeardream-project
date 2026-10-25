import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

from backend.app import crawler, main
from backend.app.history import HistoryStore


def analyze(client, monkeypatch, tmp_path):
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kw: (
        '<p id="promo" style="opacity:0">카지노 가입 보너스</p>', url))
    monkeypatch.setattr(main, 'result_path', tmp_path / 'result.json')
    response = client.post('/api/analyze', json={'url': 'https://example.com'})
    assert response.status_code == 200, response.text
    return response.json()


def test_saved_analysis_survives_store_restart_and_review_does_not_change_outputs(monkeypatch, tmp_path):
    with TestClient(main.app) as client:
        data = analyze(client, monkeypatch, tmp_path)
        assert data['analysis_id']
        original = (tmp_path / 'result.json').read_bytes()
        extra = (tmp_path / 'result_extra.json').read_bytes()
        listing = client.get('/api/history').json()
        assert listing['total'] == 1
        detail = client.get('/api/history/' + data['analysis_id']).json()
        assert detail['analysis'] == {k: v for k, v in data.items() if k != 'analysis_id'}
        assert {c['kind'] for c in detail['candidates']} == {'feature', 'content'}
        assert all(c['reviews'] == [] for c in detail['candidates'])
        path = f"/api/history/{data['analysis_id']}/candidates/{detail['candidates'][0]['id']}/reviews"
        for decision in ('promotion', 'uncertain'):
            response = client.post(path, json={'decision': decision, 'reviewer': ' 검사자 ', 'reason': ' 근거 확인 '})
            assert response.status_code == 200
            assert response.json()['reviewer'] == '검사자'
            assert response.json()['reviewed_at'].endswith('+00:00')
        reopened = HistoryStore(main.history_path).get(data['analysis_id'])
        assert [r['decision'] for r in reopened['candidates'][0]['reviews']] == ['promotion', 'uncertain']
        assert reopened['analysis'] == detail['analysis']
        assert (tmp_path / 'result.json').read_bytes() == original
        assert (tmp_path / 'result_extra.json').read_bytes() == extra
        assert client.get('/history').status_code == 200


def test_history_failure_preserves_analysis_and_downloads(monkeypatch, tmp_path):
    monkeypatch.setattr(main, 'history_path', tmp_path)  # A directory is not a database.
    with TestClient(main.app) as client:
        data = analyze(client, monkeypatch, tmp_path)
        assert data['analysis_id'] is None
        assert any('이력을 저장하지 못했습니다' in warning for warning in data['warnings'])
        assert json.loads((tmp_path / 'result.json').read_text(encoding='utf-8')) == data['result_json']
        assert client.get('/api/history').status_code == 503


def test_missing_history_and_invalid_review(monkeypatch, tmp_path):
    with TestClient(main.app) as client:
        assert client.get('/api/history/missing').status_code == 404
        data = analyze(client, monkeypatch, tmp_path)
        base = f"/api/history/{data['analysis_id']}/candidates/feature-1/reviews"
        for payload in [dict(decision='included', reviewer='a', reason='b'),
                        dict(decision='normal', reviewer=' ', reason='b'),
                        dict(decision='normal', reviewer='a', reason=''),
                        dict(decision='normal', reviewer='a' * 101, reason='b')]:
            assert client.post(base, json=payload).status_code == 422
        valid = dict(decision='uncertain', reviewer='a', reason='b')
        assert client.post(base.replace('feature-1', 'feature-999'), json=valid).status_code == 404
        assert client.post(base.replace(data['analysis_id'], 'missing'), json=valid).status_code == 404
        assert client.get('/api/history?limit=101').status_code == 422
        assert client.get('/api/history?offset=-1').status_code == 422


def test_empty_and_paginated_history(tmp_path):
    store = HistoryStore(tmp_path / 'history.sqlite3')
    assert store.list() == {'total': 0, 'items': []}
    ids = [store.save({}, {'url': str(i), 'collection_mode': 'static', 'findings': [],
                          'content_candidates': []}) for i in range(3)]
    assert store.list(1, 0)['items'][0]['id'] == ids[-1]
    assert store.list(1, 1)['items'][0]['id'] == ids[-2]
    assert store.list(1, 3)['items'] == []


def test_snapshot_tampering_and_future_schema_are_rejected(tmp_path):
    store = HistoryStore(tmp_path / 'history.sqlite3')
    key = store.save({}, {'url': 'x', 'collection_mode': 'static'})
    with sqlite3.connect(store.path) as db:
        db.execute('UPDATE analyses SET response_json=?', ('{}',))
    with pytest.raises(sqlite3.DatabaseError, match='checksum'):
        store.get(key)
    with sqlite3.connect(store.path) as db:
        db.execute('PRAGMA user_version=999')
    with pytest.raises(sqlite3.DatabaseError, match='version'):
        store.list()


def test_failed_capture_is_not_saved(monkeypatch, tmp_path):
    monkeypatch.setattr(main, 'crawl_site', lambda *a, **kw: [{'url': 'x', 'error': 'failed'}])
    with TestClient(main.app) as client:
        assert client.post('/api/analyze', json={'url': 'https://example.com'}).status_code == 502
        assert client.get('/api/history').json()['total'] == 0


def test_history_is_not_exposed_through_cross_origin_cors():
    with TestClient(main.app) as client:
        response = client.get('/api/history', headers={'Origin': 'https://unrelated.example'})
        assert 'access-control-allow-origin' not in response.headers
        response = client.options('/api/history/id/candidates/item/reviews', headers={
            'Origin': 'https://unrelated.example', 'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'content-type'})
        assert response.status_code == 400
