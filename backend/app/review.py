"""Explicit human submission decisions bound to a verified saved capture.

This workflow does not change automatic API results or accuracy labels.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import Field

from .evaluation import Technique, _hash, _replay_capture, _resolve_label
from .policy import POLICY_VERSION, assess_findings
from .result import StrictResultModel, build_result_json


class ReviewItem(StrictResultModel):
    url: str = Field(min_length=1)
    location: str = Field(min_length=1)
    technique: Technique
    source_text: str = Field(min_length=1)
    decision: Literal['pending', 'include', 'exclude'] = 'pending'
    reviewer: str = ''
    reason: str = ''
    reviewed_at: str = ''


class SubmissionReview(StrictResultModel):
    schema_version: Literal[1] = 1
    purpose: Literal['submission_review'] = 'submission_review'
    capture_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    created_at: str
    items: list[ReviewItem]


def _write_new(path, data):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2))


def initialize_submission_review(directory):
    """Create pending decisions for all replayed features; never infer approval."""
    directory = Path(directory)
    output = directory / 'submission-review.json'
    if output.exists():
        raise ValueError('Submission review already exists; existing decisions are preserved')
    raw, _, _, predictions, _ = _replay_capture(directory)
    review = SubmissionReview(
        capture_sha256=_hash(raw), created_at=datetime.now(timezone.utc).isoformat(),
        items=[ReviewItem(**{name: item[name] for name in ('url', 'location', 'technique', 'source_text')})
               for item in predictions.values()],
    ).model_dump()
    _write_new(output, review)
    return review


def export_submission_review(directory, output):
    """Export only explicit includes, with an immutable copy of all decisions.

    Pending/excluded features are absent from result.json, never implicitly false.
    The destination must be new. Validation finishes before any output is created.
    """
    directory, output = Path(directory), Path(output)
    if output.exists():
        raise ValueError('Review export already exists; choose a new output directory')
    started = datetime.now(timezone.utc).isoformat()
    raw, capture, documents, predictions, candidates = _replay_capture(directory)
    review_raw = (directory / 'submission-review.json').read_bytes()
    review = SubmissionReview.model_validate_json(review_raw)
    if review.capture_sha256 != _hash(raw):
        raise ValueError('Submission review does not belong to this capture')
    selected, seen = [], set()
    counts = {'include': 0, 'exclude': 0, 'pending': 0}
    for item in review.items:
        key = _resolve_label(item, documents)
        if key in seen:
            raise ValueError('Duplicate decisions for the same element and technique')
        seen.add(key)
        finding = predictions.get(key)
        if finding is None or item.source_text != finding['source_text']:
            raise ValueError('Review feature or original text differs from replay; initialize a new review')
        if item.decision != 'pending':
            if not item.reviewer.strip() or not item.reason.strip():
                raise ValueError('Decided items require a reviewer and reason')
            try:
                timestamp = datetime.fromisoformat(item.reviewed_at)
            except ValueError as error:
                raise ValueError('Decided items require an ISO 8601 reviewed_at timestamp') from error
            if timestamp.utcoffset() is None:
                raise ValueError('reviewed_at must include a timezone')
        counts[item.decision] += 1
        if item.decision == 'include':
            selected.append({**finding, 'is_violation': True})
    if seen != set(predictions):
        raise ValueError('Review must retain every replayed feature, including pending items')
    result = build_result_json(capture['request']['url'], selected, started_at=started)
    assessments = assess_findings(list(predictions.values()), candidates)
    audit = {
        'schema_version': 1, 'purpose': 'human_reviewed_submission',
        'capture_sha256': _hash(raw), 'review_sha256': _hash(review_raw),
        'result_sha256': _hash(json.dumps(result, ensure_ascii=False, indent=2).encode('utf-8')),
        'exported_at': result['meta']['finished_at'],
        'counts': counts, 'review_complete': counts['pending'] == 0,
        'scope': 'Replayed detected features only; not all advertisements or a legal adjudication',
        'automatic_policy_version': POLICY_VERSION,
        'automatic_assessments': assessments,
        'export_source_hashes': {
            name: _hash((Path(__file__).parent / name).read_bytes())
            for name in ('review.py', 'evaluation.py', 'detection.py', 'rendered.py', 'location.py', 'result.py',
                         'content.py', 'textnorm.py', 'policy.py', 'comparison.py')
        },
    }
    output.mkdir(parents=True, exist_ok=False)
    _write_new(output / 'result.json', result)
    # Preserve the exact reviewed bytes, including the user's formatting.
    with (output / 'submission-review.json').open('xb') as stream:
        stream.write(review_raw)
    _write_new(output / 'review-audit.json', audit)
    return audit
