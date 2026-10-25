import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

from backend.app import crawler
from backend.app.evaluation import capture_site, evaluate_capture

URL = 'https://example.test'
HTML = '''<p id="hit" style="opacity:0">Hidden</p><p id="miss" class="hidden">Missed</p>
    <p id="normal">Normal</p><p id="foreign">Привет</p><p id="unknown">ㄱ</p>'''


@pytest.fixture
def capture(monkeypatch, tmp_path):
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kwargs: (HTML, url))
    output = tmp_path / 'run'
    capture_site(URL, output)
    return output


def write_labels(directory, items, complete=False):
    document = {
        'schema_version': 1, 'purpose': 'feature_detection', 'policy': 'synthetic test policy',
        'capture_sha256': json.loads((directory / 'labels.json').read_text(encoding='utf-8'))['capture_sha256'],
        'complete': complete, 'labels': items,
    }
    (directory / 'labels.json').write_text(json.dumps(document, ensure_ascii=False), encoding='utf-8')


def label(location, expected, technique='TRANSPARENT'):
    return {'url': URL, 'location': location, 'technique': technique, 'expected': expected,
            'reviewed': True, 'reason': 'Synthetic fixture label; not a real advertising verdict'}


def test_capture_pending_labels_are_not_accuracy(capture, monkeypatch):
    def forbid_fetch(*args, **kwargs):
        pytest.fail('Offline evaluation must not fetch')

    monkeypatch.setattr(crawler, 'fetch_html', forbid_fetch)
    report = evaluate_capture(capture)
    assert report['prediction_count'] == 3
    assert report['unreviewed_labels'] == report['unjudged_predictions'] == 3
    assert report['metrics'] is None
    assert all(value == 0 for value in report['counts'].values())
    assert 'is_violation' not in report


def test_complete_review_counts_tp_fp_fn_and_explicit_tn(capture):
    write_labels(capture, [label('#hit', True), label('#miss', True), label('#normal', False),
                           label('#foreign', False, 'HOMOGLYPH')], complete=True)
    report = evaluate_capture(capture)
    assert report['counts'] == {'tp': 1, 'fp': 2, 'fn': 1, 'tn': 1}
    assert report['metrics'] == {'precision': 1 / 3, 'recall': 1 / 2, 'f1': 0.4}
    assert report['by_technique']['JAMO']['fp'] == 1
    assert report['unjudged_predictions'] == 0


def test_partial_review_does_not_call_unlabelled_predictions_false_positives(capture):
    write_labels(capture, [label('#hit', True)])
    report = evaluate_capture(capture)
    assert report['counts'] == {'tp': 1, 'fp': 0, 'fn': 0, 'tn': 0}
    assert report['unjudged_predictions'] == 2
    assert report['metrics'] is None


@pytest.mark.parametrize('items, match', [
    ([label('#missing', True)], 'one saved element'),
    ([label('p', True)], 'one saved element'),
    ([label('(', True)], 'Invalid label selector'),
    ([label('#hit', True), label('p#hit', False)], 'same element'),
    ([{**label('#hit', True), 'reason': ''}], 'reason'),
    ([{**label('#hit', True), 'expected': None}], 'Boolean'),
])
def test_invalid_review_is_rejected(capture, items, match):
    write_labels(capture, items)
    with pytest.raises(ValueError, match=match):
        evaluate_capture(capture)


def test_complete_review_requires_policy_and_reviewed_labels(capture):
    write_labels(capture, [{**label('#hit', True), 'reviewed': False}], complete=True)
    with pytest.raises(ValueError, match='Complete review'):
        evaluate_capture(capture)
    write_labels(capture, [], complete=True)
    path = capture / 'labels.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    data['policy'] = None
    path.write_text(json.dumps(data), encoding='utf-8')
    with pytest.raises(ValueError, match='policy'):
        evaluate_capture(capture)


def test_snapshot_tampering_and_run_overwrite_are_rejected(capture):
    with pytest.raises(ValueError, match='already exists'):
        capture_site(URL, capture)
    (capture / 'document-000.html').write_text('<p>Changed</p>', encoding='utf-8')
    with pytest.raises(ValueError, match='hash mismatch'):
        evaluate_capture(capture)


def test_labels_from_another_capture_are_rejected(capture):
    path = capture / 'labels.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    data['capture_sha256'] = '0' * 64
    path.write_text(json.dumps(data), encoding='utf-8')
    with pytest.raises(ValueError, match='belong'):
        evaluate_capture(capture)


def test_nested_frame_labels_can_use_equivalent_selectors(monkeypatch, tmp_path):
    documents = {
        URL: '<iframe id="outer" src="/frame"></iframe>',
        URL + '/frame': '<iframe id="inner" src="/nested"></iframe>',
        URL + '/nested': '<p id="ad" style="opacity:0">Hidden</p>',
    }
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kwargs: (documents[url], url))
    output = tmp_path / 'run'
    capture_site(URL, output)
    write_labels(output, [label('#outer >>> #inner >>> #ad', True)], complete=True)
    report = evaluate_capture(output)
    assert report['counts']['tp'] == 1
    assert report['metrics']['recall'] == 1


def test_failed_collection_cannot_be_scored_as_clean(monkeypatch, tmp_path):
    def fail(*args, **kwargs):
        raise RuntimeError('Fixture HTTP failure')

    monkeypatch.setattr(crawler, 'fetch_html', fail)
    output = tmp_path / 'run'
    data = capture_site(URL, output)
    assert data['warnings'][0]['kind'] == 'collection_failure'
    with pytest.raises(ValueError, match='No successful documents'):
        evaluate_capture(output)


def test_cli_capture_and_offline_evaluate_against_local_http(tmp_path):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            raw = '<p id="ad" style="opacity:0">Local fixture</p>'.encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(raw)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f'http://127.0.0.1:{server.server_port}'
    output = tmp_path / 'cli-run'
    root = Path(__file__).resolve().parents[1]

    def invoke(*args):
        return subprocess.run([sys.executable, '-B', 'scripts/validate_site.py', *args],
                              cwd=root, capture_output=True, text=True, timeout=20,
                              creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))

    try:
        result = invoke('capture', url, '--output', str(output))
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)['predictions'] == 1
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
    # HTTP server is stopped: replay must work without the source site.
    result = invoke('evaluate', str(output))
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['metrics'] is None
    path = output / 'labels.json'
    labels = json.loads(path.read_text(encoding='utf-8'))
    labels['policy'] = 'Synthetic fixture: inline zero opacity is a feature'
    labels['complete'] = True
    labels['labels'][0].update(expected=True, reviewed=True, reason='Synthetic inline opacity:0')
    path.write_text(json.dumps(labels), encoding='utf-8')
    result = invoke('evaluate', str(output))
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['counts']['tp'] == 1
    assert (output / 'report.json').exists()
