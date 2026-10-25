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
from .content import POLICY_VERSION, detect_content
from .comparison import evaluation_url_key
from .rendered import POLICY_VERSION as RENDERED_POLICY_VERSION

TECHNIQUES = ('HOMOGLYPH', 'JAMO', 'TRANSPARENT', 'OFFSCREEN')
Technique = Literal['HOMOGLYPH', 'JAMO', 'TRANSPARENT', 'OFFSCREEN']
CATEGORIES = ('GAMBLING', 'ADULT_CONTENT')


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


class ContentLabel(BaseModel):
    model_config = ConfigDict(extra='forbid')
    url: str = Field(min_length=1)
    location: str = Field(min_length=1)
    category: Literal['GAMBLING', 'ADULT_CONTENT']
    expected: StrictBool | None = None
    reviewed: StrictBool = False
    reason: str = ''
    # A content-presence label does not establish a legal violation.
    violation_verdict: Literal['unreviewed', 'uncertain', 'violation', 'non_violation'] = 'unreviewed'
    verdict_reason: str = ''
    reviewer: str = ''

    @property
    def technique(self):
        return self.category


class ContentLabels(Labels):
    purpose: Literal['content_detection'] = 'content_detection'
    labels: list[ContentLabel] = Field(default_factory=list)


def _hash(raw):
    return hashlib.sha256(raw).hexdigest()


def _write(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def _key(item):
    return (evaluation_url_key(item['url']), item['location'], item['technique'])


def _resolve_label(label, documents):
    path = []
    segments = label.location.split(' >>> ')
    for index, selector in enumerate(segments):
        soup = documents.get((evaluation_url_key(label.url), tuple(path)))
        try:
            matches = soup.select(selector) if soup is not None else []
        except SelectorSyntaxError as error:
            raise ValueError(f'Invalid label selector: {selector}') from error
        if len(matches) != 1 or (index < len(segments) - 1 and matches[0].name != 'iframe'):
            raise ValueError(f'Label does not identify one saved element: {label.location}')
        path.append(build_selector(matches[0]))
    return (evaluation_url_key(label.url), ' >>> '.join(path), label.technique)


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
    content_candidates = []
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
                features = detect_page(page, deadline=deadline)
                content = detect_content(page, feature_findings=features, deadline=deadline)
                predictions.extend(features)
                content_candidates.extend(content)
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
    sources = ['backend/app/detection.py', 'backend/app/content.py', 'backend/app/location.py',
               'backend/app/comparison.py', 'backend/app/browser.py', 'backend/app/rendered.py', 'backend/app/rendered_snapshot.js',
               'constraints-windows-py314.txt']
    capture = {
        'schema_version': 1, 'purpose': 'feature_detection',
        'captured_at': datetime.now(timezone.utc).isoformat(),
        'request': request.model_dump(), 'max_pages': 8, 'max_iframe_depth': 3,
        'python': platform.python_version(),
        'packages': {name: version(name) for name in ('beautifulsoup4', 'html5lib', 'soupsieve')},
        'source_hashes': {name: _hash((root / name).read_bytes()) for name in sources},
        'documents': documents, 'predictions': predictions, 'content_candidates': content_candidates,
        'content_policy_version': POLICY_VERSION, 'warnings': warnings,
        'rendered_policy_version': RENDERED_POLICY_VERSION,
    }
    _write(output / 'capture.json', capture)
    labels = Labels(capture_sha256=_hash((output / 'capture.json').read_bytes()),
                    labels=[Label(url=p['url'], location=p['location'], technique=p['technique'])
                            for p in predictions])
    _write(output / 'labels.json', labels.model_dump())
    content_labels = ContentLabels(capture_sha256=labels.capture_sha256, labels=[
        ContentLabel(url=p['url'], location=p['location'], category=p['category'])
        for p in content_candidates
    ])
    _write(output / 'content-labels.json', content_labels.model_dump())
    return capture


def _replay_capture(directory):
    """Verify and replay saved HTML without network access."""
    directory = Path(directory).resolve()
    capture_raw = (directory / 'capture.json').read_bytes()
    capture = json.loads(capture_raw.decode('utf-8'))
    if capture.get('schema_version') != 1 or capture.get('purpose') != 'feature_detection':
        raise ValueError('Unsupported capture schema')
    documents = {}
    predictions = {}
    content_candidates = []
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
        doc_key = (evaluation_url_key(record.get('top_url') or record['url']), tuple(record.get('frame_path', [])))
        soup = BeautifulSoup(page['html'], 'html5lib')
        if doc_key in documents and str(documents[doc_key]) != str(soup):
            raise ValueError('Equivalent URLs have conflicting saved document contexts')
        documents[doc_key] = soup
        features = detect_page(page)
        content_candidates.extend(detect_content(page, feature_findings=features))
        for finding in features:
            predictions[_key(finding)] = finding
    if not documents:
        raise ValueError('No successful documents to evaluate')
    return capture_raw, capture, documents, predictions, content_candidates


def initialize_content_labels(directory):
    """Create pending content labels, including for older captures; never overwrite reviews."""
    directory = Path(directory)
    output = directory / 'content-labels.json'
    if output.exists():
        raise ValueError('Content labels already exist; existing reviews are preserved')
    raw, _, _, _, candidates = _replay_capture(directory)
    labels = ContentLabels(capture_sha256=_hash(raw), labels=[
        ContentLabel(url=item['url'], location=item['location'], category=item['category'])
        for item in candidates
    ])
    # Exclusive creation also prevents accidental overwrites by concurrent callers.
    with output.open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(labels.model_dump(), ensure_ascii=False, indent=2))
    return labels.model_dump()


def evaluate_capture(directory, *, kind='feature'):
    """Score one independent label set. Content scores never adjudicate violations."""
    if kind not in {'feature', 'content'}:
        raise ValueError('Unknown evaluation kind')
    directory = Path(directory)
    capture_raw, capture, documents, predictions, content_candidates = _replay_capture(directory)
    content_mode = kind == 'content'
    model = ContentLabels if content_mode else Labels
    filename = 'content-labels.json' if content_mode else 'labels.json'
    labels_raw = (directory / filename).read_bytes()
    labels = model.model_validate_json(labels_raw.decode('utf-8'))
    if labels.capture_sha256 != _hash(capture_raw):
        raise ValueError('Labels do not belong to this capture')
    dimension = 'category' if content_mode else 'technique'
    names = CATEGORIES if content_mode else TECHNIQUES
    if content_mode:
        predictions = {(evaluation_url_key(p['url']), p['location'], p['category']): p for p in content_candidates}
    counts = {name: {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0} for name in names}
    reviewed_keys = set()
    seen_labels = set()
    details = []
    for label in labels.labels:
        if content_mode and label.violation_verdict != 'unreviewed':
            if not label.verdict_reason.strip() or not label.reviewer.strip():
                raise ValueError('A violation verdict needs a reviewer and verdict reason')
            if not label.reviewed:
                raise ValueError('A violation verdict requires a reviewed content label')
        key = (evaluation_url_key(label.url), label.location, label.technique)
        if key in seen_labels:
            raise ValueError('Duplicate label')
        seen_labels.add(key)
        if not label.reviewed:
            continue
        if label.expected is None or not label.reason.strip():
            raise ValueError('Reviewed labels need an expected Boolean and a reason')
        key = _resolve_label(label, documents)
        if key in reviewed_keys:
            raise ValueError(f'Duplicate labels identify the same element and {dimension}')
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
        'purpose': labels.purpose, 'scope': 'saved_successful_documents_only',
        'capture_sha256': _hash(capture_raw), 'captured_at': capture['captured_at'],
        'labels_sha256': _hash(labels_raw),
        'evaluator_sha256': _hash(Path(__file__).read_bytes()),
        'url_comparison_sha256': _hash(Path(__file__).with_name('comparison.py').read_bytes()),
        'rendered_detector_sha256': _hash(Path(__file__).with_name('rendered.py').read_bytes()),
        'rendered_policy_version': RENDERED_POLICY_VERSION,
        'observation_basis': {
            'rendered_documents': sum('rendered_style' in record for record in capture['documents'] if 'error' not in record),
            'static_documents': sum('rendered_style' not in record for record in capture['documents'] if 'error' not in record),
        },
        'request': capture['request'],
        'policy': labels.policy, 'review_complete': labels.complete,
        'collection_warnings': capture['warnings'], 'document_count': len(documents),
        'prediction_count': len(predictions), 'unreviewed_labels': pending,
        'content_candidate_count': len(content_candidates), 'content_candidates': content_candidates,
        'content_policy_version': POLICY_VERSION,
        'metrics_purpose': 'content_presence_only' if content_mode else 'four_technique_features_only',
        'unjudged_predictions': 0 if labels.complete else len(unknown),
        'counts': totals, f'by_{dimension}': counts,
        'metrics': metrics(totals) if labels.complete else None,
        f'metrics_by_{dimension}': {name: metrics(row) for name, row in counts.items()} if labels.complete else None,
        'details': details,
        'detector_sha256': _hash(Path(__file__).with_name('content.py' if content_mode else 'detection.py').read_bytes()),
    }
