import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

from backend.app import crawler
from backend.app.evaluation import capture_site
from backend.app.review_inventory import build_content_inventory, export_content_inventory


@pytest.fixture
def saved(monkeypatch, tmp_path):
    html = '''<title>Head ignored</title><script>ignored</script>
        <p id="hit">카지노 가입 보너스</p><p id="normal">알림 <span id="inline">학교</span><!-- ignored --></p>
        <p id="hidden" style="display:none">숨긴 안내</p>'''
    monkeypatch.setattr(crawler, 'fetch_html', lambda url, **kwargs: (html, url))
    directory = tmp_path / 'capture'
    capture_site('https://example.test', directory)
    monkeypatch.setattr(crawler, 'fetch_html', lambda *args, **kwargs: pytest.fail('Inventory must remain offline'))
    return directory


def edit_labels(directory, edit):
    path = directory / 'content-labels.json'
    data = json.loads(path.read_bytes())
    edit(data)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')


def test_inventory_includes_unpredicted_hidden_and_inline_text_without_auto_labels(saved):
    inventory = build_content_inventory(saved)
    assert inventory['block_count'] == 3
    assert inventory['category_pair_count'] == inventory['unreviewed_category_pairs'] == 6
    assert inventory['reviewed_category_pairs'] == 0 and not inventory['declared_complete']
    normal = next(unit for unit in inventory['units'] if unit['location'] == 'p#normal')
    assert normal['source_text'] == '알림 학교' and normal['predicted_categories'] == []
    ad = next(unit for unit in inventory['units'] if unit['location'] == 'p#hit')
    assert ad['predicted_categories'] == ['GAMBLING']
    assert all(label['expected'] is None and not label['reviewed'] for label in ad['labels'])
    assert normal['source_text_sha256'] == hashlib.sha256('알림 학교'.encode()).hexdigest()


def test_existing_review_is_preserved_without_replacing_answers(saved):
    def review(data):
        data['labels'][0].update(reviewed=True, expected=False, reason='Independent test reference')
    edit_labels(saved, review)
    before = (saved / 'content-labels.json').read_bytes()
    inventory = build_content_inventory(saved)
    assert inventory['reviewed_category_pairs'] == 1
    assert inventory['unreviewed_category_pairs'] == 5
    ad = next(unit for unit in inventory['units'] if unit['location'] == 'p#hit')
    assert ad['labels'][0]['expected'] is False
    assert (saved / 'content-labels.json').read_bytes() == before


@pytest.mark.parametrize('filename', ['capture.json', 'document-000.html'])
def test_invalid_binding_or_html_creates_no_inventory(saved, tmp_path, filename):
    with (saved / filename).open('ab') as stream:
        stream.write(b' ')
    output = tmp_path / 'inventory.json'
    with pytest.raises(ValueError, match='capture|hash mismatch'):
        export_content_inventory(saved, output)
    assert not output.exists()


def test_non_block_labels_are_explicitly_preserved_outside_coverage(saved):
    def review(data):
        data['labels'] = [dict(url='https://example.test', location='#inline', category='GAMBLING',
                               reviewed=True, expected=False, reason='Normal inline text')]
    edit_labels(saved, review)
    inventory = build_content_inventory(saved)
    assert inventory['reviewed_category_pairs'] == 0
    assert len(inventory['labels_outside_block_units']) == 1


def test_ambiguous_pending_aliases_are_rejected(saved):
    def duplicate(data):
        data['labels'].append({**data['labels'][0], 'location': '#hit'})
    edit_labels(saved, duplicate)
    with pytest.raises(ValueError, match='Duplicate inventory labels'):
        build_content_inventory(saved)


def test_repeated_frames_are_separate_review_units(monkeypatch, tmp_path):
    url = 'https://example.test'
    pages = {url: '<iframe src="/child"></iframe><iframe src="/child"></iframe>',
             url + '/child': '<p>정상 안내</p>'}
    monkeypatch.setattr(crawler, 'fetch_html', lambda address, **kwargs: (pages[address], address))
    directory = tmp_path / 'frames'
    capture_site(url, directory)
    inventory = build_content_inventory(directory)
    assert inventory['document_count'] == 3 and inventory['block_count'] == 2
    assert inventory['units'][0]['source_text_sha256'] == inventory['units'][1]['source_text_sha256']
    assert inventory['units'][0]['location'] != inventory['units'][1]['location']


def test_cli_utf8_exclusive_export_keeps_input_files(saved, tmp_path):
    before = {p.name: p.read_bytes() for p in saved.iterdir() if p.is_file()}
    output = tmp_path / 'inventory.json'
    script = Path(__file__).resolve().parents[1] / 'scripts/review_inventory.py'
    command = [sys.executable, '-B', str(script), str(saved), '--output', str(output)]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    raw = output.read_bytes()
    assert '알림 학교' in raw.decode('utf-8')
    assert json.loads(result.stdout)['block_count'] == 3
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode == 2 and output.read_bytes() == raw
    assert before == {p.name: p.read_bytes() for p in saved.iterdir() if p.is_file()}
