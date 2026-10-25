import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from backend.app import crawler
from backend.app.evaluation import capture_site
from backend.app.validation_suite import evaluate_suite


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def suite(monkeypatch, tmp_path):
    cases = []
    for name, html in [('ad', '<p id="hit">카지노 가입 보너스</p><p id="miss">새 표현 홍보</p>'),
                       ('normal', '<p id="normal">교육자료 안내</p>')]:
        directory = tmp_path / name
        url = f'https://example.test/{name}'
        monkeypatch.setattr(crawler, 'fetch_html', lambda address, **kwargs: (html, address))
        capture_site(url, directory)
        labels = json.loads((directory / 'content-labels.json').read_bytes())
        labels.update(complete=True, policy='Independent synthetic presence labels, not legal verdicts')
        labels['labels'] = [dict(url=url, location=selector, category=category, expected=expected,
                                 reviewed=True, reason='Synthetic reference label')
                            for selector, category, expected in (
                                [('#hit', 'GAMBLING', True), ('#miss', 'GAMBLING', True)] if name == 'ad' else
                                [('#normal', 'GAMBLING', False), ('#normal', 'ADULT_CONTENT', False)])]
        write(directory / 'content-labels.json', labels)
        cases.append(dict(id=name, directory=name, capture_sha256=digest(directory / 'capture.json'),
                          labels_sha256=digest(directory / 'content-labels.json')))
    manifest = tmp_path / 'suite.json'
    write(manifest, dict(schema_version=1, kind='content', dataset_type='synthetic',
                         scope='Synthetic saved blocks only', cases=cases))
    monkeypatch.setattr(crawler, 'fetch_html', lambda *args, **kwargs: pytest.fail('Suite must stay offline'))
    return manifest


def test_complete_micro_counts_include_real_misses(suite):
    report = evaluate_suite(suite)
    assert report['counts'] == dict(tp=1, fp=0, fn=1, tn=2)
    assert report['metrics'] == dict(precision=1, recall=0.5, f1=2/3)
    assert report['case_count'] == report['unique_page_context_count'] == 2
    assert report['by_category']['GAMBLING'] == dict(tp=1, fp=0, fn=1, tn=1)
    assert report['collection_warning_count'] == 0
    assert all(r['metrics_purpose'] == 'content_presence_only' for r in report['reports'])


def test_partial_review_cannot_produce_suite_accuracy(suite):
    document = json.loads(suite.read_bytes())
    path = suite.parent / 'ad/content-labels.json'
    labels = json.loads(path.read_bytes())
    labels['complete'] = False
    write(path, labels)
    document['cases'][0]['labels_sha256'] = digest(path)
    write(suite, document)
    report = evaluate_suite(suite)
    assert report['counts']['fn'] == 1
    assert not report['review_complete'] and report['metrics'] is None


@pytest.mark.parametrize('name', ['capture.json', 'content-labels.json', 'document-000.html'])
def test_input_mutation_is_rejected(suite, name):
    with (suite.parent / 'ad' / name).open('ab') as stream:
        stream.write(b' ')
    with pytest.raises(ValueError, match='hash mismatch'):
        evaluate_suite(suite)


@pytest.mark.parametrize('duplicate', ['id', 'directory', 'page'])
def test_repeated_cases_and_same_page_different_capture_are_rejected(suite, duplicate):
    document = json.loads(suite.read_bytes())
    if duplicate == 'page':
        shutil.copytree(suite.parent / 'ad', suite.parent / 'repeat')
        document['cases'][1] = {**document['cases'][0], 'id': 'repeat', 'directory': 'repeat'}
        # An alias capture remains the same evaluated page even if the HTML differs.
    else:
        document['cases'][1][duplicate] = document['cases'][0][duplicate]
    write(suite, document)
    with pytest.raises(ValueError, match='Duplicate|Overlapping'):
        evaluate_suite(suite)


@pytest.mark.parametrize('directory', ['../escape', ''])
def test_invalid_case_paths_are_rejected(suite, directory):
    document = json.loads(suite.read_bytes())
    document['cases'][0]['directory'] = directory
    write(suite, document)
    with pytest.raises(ValueError):
        evaluate_suite(suite)


def test_feature_suite_is_not_content_accuracy(suite):
    document = json.loads(suite.read_bytes())
    document['kind'] = 'feature'
    for case in document['cases']:
        case['labels_sha256'] = digest(suite.parent / case['directory'] / 'labels.json')
    write(suite, document)
    report = evaluate_suite(suite)
    assert report['metrics_purpose'] == 'four_technique_features_only'
    assert 'by_technique' in report and report['metrics'] is None


def test_cli_exclusive_report_preserves_inputs(suite):
    before = {p.relative_to(suite.parent): p.read_bytes() for p in suite.parent.rglob('*') if p.is_file()}
    script = Path(__file__).resolve().parents[1] / 'scripts/evaluate_suite.py'
    output = suite.parent / 'report.json'
    command = [sys.executable, '-B', str(script), str(suite), '--output', str(output)]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['counts']['fn'] == 1
    original = output.read_bytes()
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 2 and 'already exists' in result.stderr
    assert output.read_bytes() == original
    assert all((suite.parent / p).read_bytes() == raw for p, raw in before.items())
