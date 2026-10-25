"""Expose saved text blocks for review, including blocks with no predictions."""

import json
from pathlib import Path

from .content import _text_units
from .evaluation import CATEGORIES, ContentLabel, ContentLabels, _hash, _replay_capture, _resolve_label, evaluate_capture
from .comparison import evaluation_url_key
from .location import build_selector


def build_content_inventory(directory):
    directory = Path(directory)
    capture_raw, capture, documents, _, candidates = _replay_capture(directory)
    labels_raw = (directory / 'content-labels.json').read_bytes()
    labels = ContentLabels.model_validate_json(labels_raw)
    # Reuse the label/verdict/selector checks of scoring; never reinterpret bad
    # or incomplete labels as a negative reference answer.
    report = evaluate_capture(directory, kind='content')
    if report['capture_sha256'] != _hash(capture_raw) or report['labels_sha256'] != _hash(labels_raw):
        raise ValueError('Capture or labels changed during inventory creation')
    known = {}
    for label in labels.labels:
        key = _resolve_label(label, documents)
        if key in known:
            raise ValueError('Duplicate inventory labels identify the same element/category')
        known[key] = label
    predictions = {(evaluation_url_key(item['url']), item['location'], item['category']) for item in candidates}
    # Use original collected URL strings; equivalence keys are only for lookup.
    urls = {evaluation_url_key(record.get('top_url') or record['url']): record.get('top_url') or record['url']
            for record in capture['documents'] if 'error' not in record}
    units, covered = [], set()
    for (url_key, frame_path), soup in documents.items():
        for owner, parts in _text_units(soup, None):
            text = ''.join(parts)
            if not text.strip():
                continue
            location = ' >>> '.join([*frame_path, build_selector(owner)])
            items = []
            for category in CATEGORIES:
                key = (url_key, location, category)
                label = known.get(key) or ContentLabel(url=urls[url_key], location=location, category=category)
                covered.add(key)
                items.append(label.model_dump())
            units.append(dict(url=urls[url_key], location=location, source_text=text,
                source_text_sha256=_hash(text.encode('utf-8')), labels=items,
                predicted_categories=[category for category in CATEGORIES if (url_key, location, category) in predictions]))
    reviewed = sum(item['reviewed'] for unit in units for item in unit['labels'])
    return dict(schema_version=1, purpose='saved_content_review_inventory',
        scope='Saved nonempty text blocks only; not a complete website, image, dynamic or legal review',
        capture_sha256=_hash(capture_raw), labels_sha256=_hash(labels_raw),
        inventory_code_sha256=_hash(Path(__file__).read_bytes()),
        content_policy_version=report['content_policy_version'],
        document_count=len(documents), block_count=len(units), category_pair_count=len(units) * len(CATEGORIES),
        reviewed_category_pairs=reviewed, unreviewed_category_pairs=len(units) * len(CATEGORIES) - reviewed,
        declared_complete=labels.complete, collection_warnings=capture['warnings'],
        labels_outside_block_units=[label.model_dump() for key, label in known.items() if key not in covered],
        units=units)


def export_content_inventory(directory, output):
    output = Path(output)
    if output.exists():
        raise ValueError('Inventory already exists; choose a new output path')
    inventory = build_content_inventory(directory)
    with output.open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(inventory, stream, ensure_ascii=False, indent=2)
    return inventory
