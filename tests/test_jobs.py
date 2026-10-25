import time
from threading import Event

from fastapi.testclient import TestClient

from backend.app import crawler, main
from backend.app.models import JobRequest


def finished(client, job_id):
    limit = time.monotonic() + 5
    while time.monotonic() < limit:
        snapshot = client.get('/api/jobs/' + job_id).json()
        if snapshot['status'] in {'completed', 'cancelled', 'failed'}:
            return snapshot
        time.sleep(.01)
    raise AssertionError('Fixture job did not finish')


def test_live_progress_cancel_returns_only_completed_documents(monkeypatch, tmp_path):
    second_started = Event()
    def fetch(url, **kw):
        if url.endswith('/slow'):
            second_started.set()
            kw['deadline'].cancel_event.wait(3)
            kw['deadline'].check()
        return '<p style="opacity:0">카지노 가입 보너스</p><a href="/slow">Slow</a><a href="/later">Later</a>', url
    monkeypatch.setattr(crawler, 'fetch_html', fetch)
    monkeypatch.setattr(main, 'result_path', tmp_path / 'result.json')
    with TestClient(main.app) as client:
        response = client.post('/api/jobs', json={'url': 'https://example.com'})
        assert response.status_code == 202
        job_id = response.json()['id']
        try:
            assert second_started.wait(2)
            progress = client.get('/api/jobs/' + job_id).json()
            assert progress['status'] == 'running'
            assert progress['progress']['analyzed_documents'] == 1
            assert progress['progress']['current_url'].endswith('/slow')
            assert progress['request']['max_pages'] == 100
            assert progress['request']['total_timeout_sec'] == 1500
            assert client.post('/api/jobs', json={'url': 'https://example.com'}).status_code == 409
            assert client.post('/api/analyze', json={'url': 'https://example.com'}).status_code == 409
        finally:
            assert client.post(f'/api/jobs/{job_id}/cancel').status_code == 200
            result = finished(client, job_id)
        assert result['status'] == 'cancelled'
        assert result['result']['coverage']['analyzed_documents'] == 1
        assert result['result']['coverage']['failed_documents'] == 1
        assert len(result['result']['result_json']['findings']) == 1
        assert any('사용자 요청' in w for w in result['result']['warnings'])
        assert result['result']['analysis_id']
        assert client.post(f'/api/jobs/{job_id}/cancel').json()['status'] == 'cancelled'


def test_cancel_before_first_analysis_keeps_previous_results(monkeypatch, tmp_path):
    started = Event()
    def fetch(url, **kw):
        started.set()
        kw['deadline'].cancel_event.wait(3)
        kw['deadline'].check()
        return '<p>Late</p>', url
    monkeypatch.setattr(crawler, 'fetch_html', fetch)
    path = tmp_path / 'result.json'
    path.write_text('previous', encoding='utf-8')
    monkeypatch.setattr(main, 'result_path', path)
    with TestClient(main.app) as client:
        job_id = client.post('/api/jobs', json={'url': 'https://example.com'}).json()['id']
        try:
            assert started.wait(2)
        finally:
            client.post(f'/api/jobs/{job_id}/cancel')
            result = finished(client, job_id)
        assert result['status'] == 'cancelled'
        assert result['result'] is None
        assert path.read_text(encoding='utf-8') == 'previous'
        assert client.get('/api/history').json()['total'] == 0


def test_completed_and_failed_jobs_and_invalid_limits(monkeypatch, tmp_path):
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kw: ('<p>OK</p>', url))
    monkeypatch.setattr(main, 'result_path', tmp_path / 'result.json')
    with TestClient(main.app) as client:
        assert client.get('/api/jobs/missing').status_code == 404
        assert client.post('/api/jobs/missing/cancel').status_code == 404
        for field, value in [('max_pages', 0), ('max_pages', 1001), ('max_depth', 21), ('total_timeout_sec', 1801)]:
            assert client.post('/api/jobs', json={'url': 'https://example.com', field: value}).status_code == 422
        job_id = client.post('/api/jobs', json={'url': 'https://example.com', 'max_pages': 1}).json()['id']
        result = finished(client, job_id)
        assert result['status'] == 'completed'
        assert result['progress']['analyzed_documents'] == 1
        assert result['result']['coverage']['limits']['max_documents'] == 1
        assert result['result']['coverage']['website_complete'] is False
        monkeypatch.setattr(main, 'crawl_site', lambda *a, **kw: [{'url': 'x', 'error': 'fixture'}])
        job_id = client.post('/api/jobs', json={'url': 'https://example.com'}).json()['id']
        result = finished(client, job_id)
        assert result['status'] == 'failed'
        assert result['error']['status_code'] == 502


def test_in_memory_job_results_are_bounded(monkeypatch, tmp_path):
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kw: ('<p>OK</p>', url))
    monkeypatch.setattr(main, 'result_path', tmp_path / 'result.json')
    with TestClient(main.app) as client:
        ids = []
        for _ in range(21):
            ids.append(client.post('/api/jobs', json={'url': 'https://example.com', 'max_pages': 1}).json()['id'])
            assert finished(client, ids[-1])['status'] == 'completed'
        assert client.get('/api/jobs/' + ids[0]).status_code == 404
        assert client.get('/api/history').json()['total'] == 21
