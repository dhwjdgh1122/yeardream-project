"""Save collection inputs and compare feature findings with reviewed labels."""

import hashlib
import json
import platform
from contextlib import nullcontext
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from typing import Literal

from bs4 import BeautifulSoup
from pydantic import BaseModel, ConfigDict, Field, StrictBool
from soupsieve import SelectorSyntaxError

from .browser import BrowserRenderer
from .crawler import crawl_site, normalize_url
from .detection import detect_page
from .limits import AnalysisTimeout, Deadline
from .models import AnalyzeRequest
from .location import build_selector

TECHNIQUES = ('HOMOGLYPH', 'JAMO', 'TRANSPARENT', 'OFFSCREEN')
Technique = Literal['HOMOGLYPH', 'JAMO', 'TRANSPARENT', 'OFFSCREEN']


class Label(BaseModel):
    model_config = ConfigDict(extra='forbid')
    url: str = Field(min_length=1)
    location: str = Field(min_length=1)
    technique: Technique
    expected: StrictBool | None = None
    reviewed: StrictBool = False
    reason: str = ''


class Labels(BaseModel):
    model_config = ConfigDict(extra='forbid')
    schema_version: Literal[1] = 1
    purpose: Literal['feature_detection'] = 'feature_detection'
    capture_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    policy: str | None = None
    complete: StrictBool = False
    labels: list[Label] = Field(default_factory=list)


def _hash(raw):
    return hashlib.sha256(raw).hexdigest()


def _write(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def _key(item):
    return (item['url'], item['location'], item['technique'])


def _resolve_label(label, documents):
    path = []
    segments = label.location.split(' >>> ')
    for index, selector in enumerate(segments):
        soup = documents.get((label.url, tuple(path)))
        try:
            matches = soup.select(selector) if soup is not None else []
        except SelectorSyntaxError as error:
            raise ValueError(f'Invalid label selector: {selector}') from error
        if len(matches) != 1 or (index < len(segments) - 1 and matches[0].name != 'iframe'):
            raise ValueError(f'Label does not identify one saved element: {label.location}')
        path.append(build_selector(matches[0]))
    return (label.url, ' >>> '.join(path), label.technique)


def capture_site(url, output, *, mode='static', max_depth=0, total_timeout_sec=60, render_wait_ms=500):
    """Capture one bounded run. Existing runs and result.json are never replaced."""
    request = AnalyzeRequest(url=normalize_url(url), collection_mode=mode, max_depth=max_depth,
                             total_timeout_sec=total_timeout_sec, render_wait_ms=render_wait_ms)
    output = Path(output)
    if output.exists():
        raise ValueError('Capture output already exists; choose a new run directory')
    deadline = Deadline.after(request.total_timeout_sec)
    rendering = BrowserRenderer(deadline, request.render_wait_ms) if mode == 'browser' else nullcontext(None)
    with rendering as renderer:
        pages = crawl_site(request.url, max_pages=8, max_depth=request.max_depth,
                           deadline=deadline, renderer=renderer)
    documents = []
    predictions = []
    warnings = []
    output.mkdir(parents=True)
    for index, page in enumerate(pages):
        record = {key: value for key, value in page.items() if key not in {'html', 'text'}}
        if 'error' in page:
            warnings.append({'kind': 'collection_failure', 'url': page['url'], 'error': page['error']})
        else:
            raw = page['html'].encode('utf-8')
            record['file'] = f'document-{index:03d}.html'
            record['sha256'] = _hash(raw)
            (output / record['file']).write_bytes(raw)
            try:
                predictions.extend(detect_page(page, deadline=deadline))
            except AnalysisTimeout:
                record['detection_incomplete'] = True
                warnings.append({'kind': 'detection_timeout', 'url': page['url']})
        for key in ('frame_omissions', 'link_omissions', 'collection_warnings'):
            if page.get(key):
                warnings.append({'kind': key, 'url': page['url'], 'details': page[key]})
        if page.get('crawl_truncated'):
            warnings.append({'kind': page.get('crawl_stop_reason', 'max_pages'), 'url': page['url']})
        documents.append(record)
    predictions = list({_key(item): item for item in predictions}.values())
    root = Path(__file__).resolve().parents[2]
    sources = ['backend/app/detection.py', 'backend/app/location.py', 'constraints-windows-py314.txt']
    capture = {
        'schema_version': 1, 'purpose': 'feature_detection',
        'captured_at': datetime.now(timezone.utc).isoformat(),
        'request': request.model_dump(), 'max_pages': 8, 'max_iframe_depth': 3,
        'python': platform.python_version(),
        'packages': {name: version(name) for name in ('beautifulsoup4', 'html5lib', 'soupsieve')},
        'source_hashes': {name: _hash((root / name).read_bytes()) for name in sources},
        'documents': documents, 'predictions': predictions, 'warnings': warnings,
    }
    _write(output / 'capture.json', capture)
    labels = Labels(capture_sha256=_hash((output / 'capture.json').read_bytes()),
                    labels=[Label(url=p['url'], location=p['location'], technique=p['technique'])
                            for p in predictions])
    _write(output / 'labels.json', labels.model_dump())
    return capture


def evaluate_capture(directory):
    """Replay saved HTML; this function never performs a network request."""
    directory = Path(directory).resolve()
    capture_raw = (directory / 'capture.json').read_bytes()
    capture = json.loads(capture_raw.decode('utf-8'))
    if capture.get('schema_version') != 1 or capture.get('purpose') != 'feature_detection':
        raise ValueError('Unsupported capture schema')
    labels = Labels.model_validate_json((directory / 'labels.json').read_text(encoding='utf-8'))
    if labels.capture_sha256 != _hash(capture_raw):
        raise ValueError('Labels do not belong to this capture')
    documents = {}
    predictions = {}
    for record in capture['documents']:
        if 'error' in record:
            continue
        path = (directory / record['file']).resolve()
        if not path.is_relative_to(directory):
            raise ValueError('Snapshot file must be inside the capture directory')
        raw = path.read_bytes()
        if _hash(raw) != record['sha256']:
            raise ValueError(f'Snapshot hash mismatch: {record["file"]}')
        page = {**record, 'html': raw.decode('utf-8')}
        doc_key = (record.get('top_url') or record['url'], tuple(record.get('frame_path', [])))
        if doc_key in documents:
            raise ValueError('Duplicate document context')
        documents[doc_key] = BeautifulSoup(page['html'], 'html5lib')
        for finding in detect_page(page):
            predictions[_key(finding)] = finding
    if not documents:
        raise ValueError('No successful documents to evaluate')
    counts = {name: {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0} for name in TECHNIQUES}
    reviewed_keys = set()
    seen_labels = set()
    details = []
    for label in labels.labels:
        key = (label.url, label.location, label.technique)
        if key in seen_labels:
            raise ValueError('Duplicate label')
        seen_labels.add(key)
        if not label.reviewed:
            continue
        if label.expected is None or not label.reason.strip():
            raise ValueError('Reviewed labels need an expected Boolean and a reason')
        key = _resolve_label(label, documents)
        if key in reviewed_keys:
            raise ValueError('Duplicate labels identify the same element and technique')
        reviewed_keys.add(key)
        predicted = key in predictions
        outcome = ('tp' if predicted else 'fn') if label.expected else ('fp' if predicted else 'tn')
        counts[label.technique][outcome] += 1
        details.append({**label.model_dump(), 'canonical_location': key[1], 'predicted': predicted, 'outcome': outcome})
    pending = sum(not label.reviewed for label in labels.labels)
    unknown = set(predictions) - reviewed_keys
    if labels.complete:
        if pending or not labels.policy or not labels.policy.strip():
            raise ValueError('Complete review requires a policy and no unreviewed labels')
        for key in sorted(unknown):
            counts[key[2]]['fp'] += 1
            details.append({**predictions[key], 'outcome': 'fp', 'reason': 'Outside exhaustive positive labels'})
    totals = {key: sum(row[key] for row in counts.values()) for key in ('tp', 'fp', 'fn', 'tn')}

    def metrics(row):
        tp, fp, fn = row['tp'], row['fp'], row['fn']
        return {
            'precision': tp / (tp + fp) if tp + fp else None,
            'recall': tp / (tp + fn) if tp + fn else None,
            'f1': 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None,
        }

    return {
        'purpose': 'feature_detection', 'scope': 'saved_successful_documents_only',
        'capture_sha256': _hash(capture_raw), 'captured_at': capture['captured_at'],
        'request': capture['request'],
        'policy': labels.policy, 'review_complete': labels.complete,
        'collection_warnings': capture['warnings'], 'document_count': len(documents),
        'prediction_count': len(predictions), 'unreviewed_labels': pending,
        'unjudged_predictions': 0 if labels.complete else len(unknown),
        'counts': totals, 'by_technique': counts,
        'metrics': metrics(totals) if labels.complete else None,
        'metrics_by_technique': {name: metrics(row) for name, row in counts.items()} if labels.complete else None,
        'details': details,
        'detector_sha256': _hash(Path(__file__).with_name('detection.py').read_bytes()),
    }
