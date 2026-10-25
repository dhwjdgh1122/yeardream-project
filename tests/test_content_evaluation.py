import json
import subprocess
import sys
from pathlib import Path

import pytest

from backend.app import crawler
from backend.app.evaluation import capture_site, evaluate_capture, initialize_content_labels

URL = 'https://example.test'
HTML = '''<p id="gambling">카지노 신규가입 보너스</p>
<p id="adult">성인영상 무료시청</p><p id="miss">배팅방 회원 모집</p>
<p id="normal">도박 예방교육 안내</p>'''


@pytest.fixture
def capture(monkeypatch, tmp_path):
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kwargs: (HTML, url))
    output = tmp_path / 'run'
    capture_site(URL, output)
    return output


def label(location, expected, category='GAMBLING', **kwargs):
    return dict(url=URL, location=location, category=category, expected=expected,
                reviewed=True, reason='Synthetic content-presence review', **kwargs)


def write_labels(directory, items, complete=False, **kwargs):
    path = directory / 'content-labels.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    data.update(labels=items, complete=complete, policy='Synthetic exhaustive fixture policy')
    data.update(kwargs)
    path.write_text(json.dumps(data), encoding='utf-8')


def test_pending_content_is_separate_and_offline(capture, monkeypatch):
    def fail(*args, **kwargs):
        pytest.fail('Evaluation must remain offline')
    monkeypatch.setattr(crawler, 'fetch_html', fail)
    report = evaluate_capture(capture, kind='content')
    assert report['purpose'] == 'content_detection'
    assert report['metrics_purpose'] == 'content_presence_only'
    assert report['prediction_count'] == report['unreviewed_labels'] == 2
    assert report['metrics'] is None
    assert evaluate_capture(capture)['prediction_count'] == 0
    assert 'is_violation' not in report


def test_exhaustive_content_counts_include_missed_positive_and_unlabelled_fp(capture):
    # Deliberately judge the adult prediction false by omitting it from positives.
    write_labels(capture, [label('#gambling', True), label('#miss', True),
                           label('#normal', False)], complete=True)
    report = evaluate_capture(capture, kind='content')
    assert report['counts'] == dict(tp=1, fp=1, fn=1, tn=1)
    assert report['metrics'] == dict(precision=0.5, recall=0.5, f1=0.5)
    assert report['by_category']['ADULT_CONTENT']['fp'] == 1
    assert report['metrics_by_category']['ADULT_CONTENT']['recall'] is None


def test_partial_content_keeps_unknown_predictions_unjudged(capture):
    write_labels(capture, [label('#gambling', True)])
    report = evaluate_capture(capture, kind='content')
    assert report['counts'] == dict(tp=1, fp=0, fn=0, tn=0)
    assert report['unjudged_predictions'] == 1
    assert report['metrics'] is None
    assert report['details'][0]['violation_verdict'] == 'unreviewed'


@pytest.mark.parametrize('items, kwargs, match', [
    ([label('#missing', True)], {}, 'one saved element'),
    ([label('p', True)], {}, 'one saved element'),
    ([label('#gambling', True), label('p#gambling', False)], {}, 'same element'),
    ([dict(label('#gambling', True), expected=None)], {}, 'Boolean'),
    ([dict(label('#gambling', True), reason='')], {}, 'reason'),
    ([label('#gambling', True)], {'capture_sha256': '0' * 64}, 'belong'),
    ([dict(label('#gambling', True), expected='true')], {}, 'boolean'),
    ([label('#gambling', True)], {'complete': True, 'policy': ''}, 'policy'),
    ([dict(label('#gambling', True), reviewed=False)], {'complete': True}, 'unreviewed'),
    ([label('#gambling', True, violation_verdict='violation')], {}, 'reviewer'),
    ([dict(label('#gambling', True), reviewed=False, violation_verdict='uncertain',
           verdict_reason='Need authority review', reviewer='fixture')], {}, 'reviewed content'),
])
def test_invalid_content_review_is_rejected(capture, items, kwargs, match):
    write_labels(capture, items, **kwargs)
    with pytest.raises(ValueError, match=match):
        evaluate_capture(capture, kind='content')


def test_human_verdict_is_recorded_but_does_not_change_content_metrics(capture):
    write_labels(capture, [label('#gambling', True, violation_verdict='uncertain',
                                verdict_reason='Synthetic review needs further evidence', reviewer='fixture')])
    report = evaluate_capture(capture, kind='content')
    assert report['counts']['tp'] == 1
    assert report['details'][0]['violation_verdict'] == 'uncertain'
    assert report['metrics'] is None


def test_initialize_old_capture_and_preserve_existing_reviews(capture):
    path = capture / 'content-labels.json'
    original = path.read_bytes()
    with pytest.raises(ValueError, match='already exist'):
        initialize_content_labels(capture)
    assert path.read_bytes() == original
    path.unlink()
    assert len(initialize_content_labels(capture)['labels']) == 2
    assert path.read_bytes() == original


def test_content_replay_rejects_tampered_html(capture):
    (capture / 'document-000.html').write_text('<p>Changed</p>', encoding='utf-8')
    with pytest.raises(ValueError, match='hash mismatch'):
        evaluate_capture(capture, kind='content')


def test_nested_frame_content_label_alias(monkeypatch, tmp_path):
    pages = {URL: '<iframe id="frame" src="/frame"></iframe>', URL + '/frame': HTML}
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kwargs: (pages[url], url))
    output = tmp_path / 'frames'
    capture_site(URL, output)
    write_labels(output, [label('iframe#frame >>> p#gambling', True)])
    assert evaluate_capture(output, kind='content')['counts']['tp'] == 1


def test_cli_content_report_does_not_replace_feature_report(capture):
    root = Path(__file__).resolve().parents[1]
    sentinel = capture / 'report.json'
    sentinel.write_text('existing feature report', encoding='utf-8')
    result = subprocess.run([sys.executable, '-B', 'scripts/validate_site.py', 'evaluate',
                             str(capture), '--kind', 'content'], cwd=root,
                            capture_output=True, text=True, timeout=20,
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['prediction_count'] == 2
    assert (capture / 'content-report.json').exists()
    assert sentinel.read_text(encoding='utf-8') == 'existing feature report'
