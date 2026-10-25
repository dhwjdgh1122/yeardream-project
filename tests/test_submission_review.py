import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from backend.app import crawler
from backend.app.evaluation import capture_site
from backend.app.review import export_submission_review, initialize_submission_review


@pytest.fixture
def run(monkeypatch, tmp_path):
    html = '<p id="unknown" style="opacity:0">  새 표현 광고\n원문  </p><p id="auto">ㅋㅏㅈㅣㄴㅗ 보너스</p>'
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kwargs: (html, url))
    directory = tmp_path / 'capture'
    capture_site('https://example.test', directory)
    initialize_submission_review(directory)
    monkeypatch.setattr(crawler, 'fetch_html', lambda *args, **kwargs: pytest.fail('Must remain offline'))
    return directory


def edit(run, change):
    path = run / 'submission-review.json'
    review = json.loads(path.read_bytes())
    change(review)
    path.write_text(json.dumps(review, ensure_ascii=False), encoding='utf-8')


def decide(item, decision='include'):
    item.update(decision=decision, reviewer='Synthetic reviewer', reason='Synthetic decision, not a real legal verdict',
                reviewed_at='2026-10-25T13:00:00+09:00')


def test_pending_never_inherits_automatic_inclusion(run, tmp_path):
    before = {p.name: p.read_bytes() for p in run.iterdir()}
    assert all(item['decision'] == 'pending' for item in json.loads(before['submission-review.json'])['items'])
    output = tmp_path / 'export'
    audit = export_submission_review(run, output)
    assert audit['counts'] == {'include': 0, 'exclude': 0, 'pending': 2}
    assert not audit['review_complete']
    assert json.loads((output / 'result.json').read_bytes())['findings'] == []
    assert any(a['submission_status'] == 'included' for a in audit['automatic_assessments'])
    assert before == {p.name: p.read_bytes() for p in run.iterdir()}


def test_explicit_override_original_text_and_audit(run, tmp_path):
    def decisions(review):
        for item in review['items']:
            decide(item, 'include' if item['location'] == 'p#unknown' else 'exclude')
        # Equivalent URL and selector resolve to the same saved element.
        next(item for item in review['items'] if item['location'] == 'p#unknown').update(
            url='http://example.test/#fragment', location='#unknown')
    edit(run, decisions)
    output = tmp_path / 'export'
    audit = export_submission_review(run, output)
    assert audit['review_complete']
    assert audit['counts'] == {'include': 1, 'exclude': 1, 'pending': 0}
    findings = json.loads((output / 'result.json').read_bytes())['findings']
    assert len(findings) == 1 and findings[0]['is_violation'] is True
    assert findings[0]['evidence_text'] == '  새 표현 광고\n원문  '
    assert findings[0]['location'] == 'p#unknown'
    for filename, hash_field in [('result.json', 'result_sha256'), ('submission-review.json', 'review_sha256')]:
        assert hashlib.sha256((output / filename).read_bytes()).hexdigest() == audit[hash_field]
    assert (output / 'submission-review.json').read_bytes() == (run / 'submission-review.json').read_bytes()


@pytest.mark.parametrize('field,value', [
    ('reviewer', '  '), ('reason', ''), ('reviewed_at', ''),
    ('reviewed_at', '2026-10-25T12:00:00'), ('decision', 'true'),
    ('source_text', 'changed'), ('location', '#missing'), ('technique', 'OFFSCREEN'),
    ('url', 'https://other.test'),
])
def test_invalid_decisions_create_no_output(run, tmp_path, field, value):
    def mutate(review):
        decide(review['items'][0])
        review['items'][0][field] = value
    edit(run, mutate)
    output = tmp_path / 'export'
    with pytest.raises(ValueError):
        export_submission_review(run, output)
    assert not output.exists()


@pytest.mark.parametrize('mutation', ['capture', 'html', 'duplicate', 'missing'])
def test_binding_and_complete_inventory(run, tmp_path, mutation):
    if mutation == 'capture':
        edit(run, lambda review: review.update(capture_sha256='0' * 64))
    elif mutation == 'html':
        (run / 'document-000.html').write_text('tampered', encoding='utf-8')
    elif mutation == 'duplicate':
        edit(run, lambda review: review['items'].append({
            **next(item for item in review['items'] if item['location'] == 'p#unknown'), 'location': '#unknown'}))
    else:
        edit(run, lambda review: review['items'].pop())
    with pytest.raises(ValueError):
        export_submission_review(run, tmp_path / 'export')
    assert not (tmp_path / 'export').exists()


def test_existing_reviews_and_exports_are_preserved(run, tmp_path):
    original = (run / 'submission-review.json').read_bytes()
    with pytest.raises(ValueError, match='already exists'):
        initialize_submission_review(run)
    assert (run / 'submission-review.json').read_bytes() == original
    output = tmp_path / 'export'
    export_submission_review(run, output)
    before = {p.name: p.read_bytes() for p in output.iterdir()}
    with pytest.raises(ValueError, match='already exists'):
        export_submission_review(run, output)
    assert before == {p.name: p.read_bytes() for p in output.iterdir()}


def test_cli_export_and_error(run, tmp_path):
    script = Path(__file__).resolve().parents[1] / 'scripts/review_submission.py'
    args = [sys.executable, '-B', str(script), 'export', str(run), '--output', str(tmp_path / 'cli-export')]
    result = subprocess.run(args, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['counts']['pending'] == 2
    result = subprocess.run(args, capture_output=True, text=True)
    assert result.returncode == 2 and 'already exists' in result.stderr


def test_nested_frame_decisions_remain_in_correct_context(monkeypatch, tmp_path):
    url = 'https://example.test'
    pages = {
        url: '<iframe id="outer" src="/frame"></iframe>',
        url + '/frame': '<iframe id="inner" src="/nested"></iframe>',
        url + '/nested': '<p id="ad" style="opacity:0">ㅋㅏㅈㅣㄴㅗ 보너스</p>',
    }
    monkeypatch.setattr(crawler, 'fetch_html', lambda address, **kwargs: (pages[address], address))
    directory = tmp_path / 'frames'
    capture_site(url, directory)
    review = initialize_submission_review(directory)
    assert len(review['items']) == 2
    assert all(item['location'].count(' >>> ') == 2 for item in review['items'])
    edit(directory, lambda data: [decide(item) for item in data['items']])
    output = tmp_path / 'export'
    export_submission_review(directory, output)
    findings = json.loads((output / 'result.json').read_bytes())['findings']
    assert {item['technique'] for item in findings} == {'JAMO', 'TRANSPARENT'}
    assert all(item['url'] == url for item in findings)


def test_empty_capture_cli_initialization(monkeypatch, tmp_path):
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kwargs: ('<p>정상 안내</p>', url))
    directory = tmp_path / 'empty'
    capture_site('https://example.test', directory)
    script = Path(__file__).resolve().parents[1] / 'scripts/review_submission.py'
    args = [sys.executable, '-B', str(script), 'init', str(directory)]
    result = subprocess.run(args, capture_output=True, text=True)
    assert result.returncode == 0 and json.loads(result.stdout)['pending'] == 0
    result = subprocess.run(args, capture_output=True, text=True)
    assert result.returncode == 2 and 'already exists' in result.stderr
    audit = export_submission_review(directory, tmp_path / 'export')
    assert audit['review_complete'] and sum(audit['counts'].values()) == 0
    assert 'detected features only' in audit['scope']
