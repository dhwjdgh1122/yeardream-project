"""Re-evaluate a pinned saved dataset without counting repeated pages twice."""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import Field

from .comparison import evaluation_url_key
from .evaluation import _hash, evaluate_capture
from .result import StrictResultModel


class SuiteCase(StrictResultModel):
    id: str = Field(min_length=1)
    directory: str = Field(min_length=1)
    capture_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    labels_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')


class ValidationSuite(StrictResultModel):
    schema_version: Literal[1] = 1
    kind: Literal['feature', 'content']
    dataset_type: Literal['real_saved_pages', 'synthetic']
    scope: str = Field(min_length=1)
    cases: list[SuiteCase] = Field(min_length=1)


def _metrics(counts):
    tp, fp, fn = (counts[key] for key in ('tp', 'fp', 'fn'))
    return {
        'precision': tp / (tp + fp) if tp + fp else None,
        'recall': tp / (tp + fn) if tp + fn else None,
        'f1': 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None,
    }


def summarize_content_repetition(reports):
    """Describe exact-text repetition without merging scored DOM locations.

    This is a diagnostic for predicted content, not dataset independence or
    accuracy. Whitespace/Unicode differences are deliberately preserved.
    """
    groups = {}
    for report in reports:
        for candidate in report['content_candidates']:
            text = candidate.get('source_text')
            if not isinstance(text, str) or not text:
                raise ValueError('Repetition diagnostics require original source_text')
            key = (candidate['category'], _hash(text.encode('utf-8')))
            group = groups.setdefault(key, {'category': key[0], 'source_text_sha256': key[1], 'occurrences': []})
            group['occurrences'].append({
                'case_id': report['case_id'], 'url': candidate['url'], 'location': candidate['location'],
            })
    repeated = []
    for key in sorted(groups):
        group = groups[key]
        count = len(group['occurrences'])
        if count > 1:
            case_ids = sorted({item['case_id'] for item in group['occurrences']})
            repeated.append({**group, 'occurrence_count': count, 'case_count': len(case_ids), 'case_ids': case_ids})
    return {
        'basis': 'Predicted category + exact original UTF-8 text; not semantic uniqueness or independent samples',
        'prediction_count': sum(len(group['occurrences']) for group in groups.values()),
        'unique_category_text_count': len(groups),
        'repeated_category_text_group_count': len(repeated),
        'occurrences_in_repeated_groups': sum(group['occurrence_count'] for group in repeated),
        'additional_repeated_occurrences': sum(group['occurrence_count'] - 1 for group in repeated),
        'groups': repeated,
    }


def evaluate_suite(manifest_path):
    """Pinned captures/labels are inputs; no files are written and no sites fetched."""
    manifest_path = Path(manifest_path).resolve()
    raw = manifest_path.read_bytes()
    suite = ValidationSuite.model_validate_json(raw)
    if not suite.scope.strip():
        raise ValueError('Suite scope must describe the reviewed dataset')
    ids, paths, page_owners = set(), set(), {}
    reports = []
    filename = 'content-labels.json' if suite.kind == 'content' else 'labels.json'
    for case in suite.cases:
        directory = (manifest_path.parent / case.directory).resolve()
        if Path(case.directory).is_absolute() or not directory.is_relative_to(manifest_path.parent):
            raise ValueError('Case directory must stay inside the suite directory')
        if case.id in ids or directory in paths:
            raise ValueError('Duplicate suite case ID or directory')
        ids.add(case.id)
        paths.add(directory)
        capture_raw = (directory / 'capture.json').read_bytes()
        if _hash(capture_raw) != case.capture_sha256:
            raise ValueError(f'Capture hash mismatch: {case.id}')
        if _hash((directory / filename).read_bytes()) != case.labels_sha256:
            raise ValueError(f'Labels hash mismatch: {case.id}')
        capture = json.loads(capture_raw)
        for document in capture['documents']:
            if 'error' in document:
                continue
            # Comparing whole top-level page contexts is conservative: repeated
            # captures/modes/query aliases must not inflate the dataset size.
            key = evaluation_url_key(document.get('top_url') or document['url'])
            if key in page_owners and page_owners[key] != case.id:
                raise ValueError(f'Overlapping page contexts in {page_owners[key]} and {case.id}')
            page_owners[key] = case.id
        report = evaluate_capture(directory, kind=suite.kind)
        reports.append({'case_id': case.id, 'directory': case.directory, **report})
    totals = {name: sum(report['counts'][name] for report in reports) for name in ('tp', 'fp', 'fn', 'tn')}
    complete = all(report['review_complete'] for report in reports)
    dimension = 'category' if suite.kind == 'content' else 'technique'
    names = reports[0][f'by_{dimension}']
    grouped = {name: {key: sum(report[f'by_{dimension}'][name][key] for report in reports)
                      for key in totals} for name in names}
    return {
        'schema_version': 1, 'purpose': 'saved_validation_suite',
        'evaluated_at': datetime.now(timezone.utc).isoformat(),
        'kind': suite.kind, 'dataset_type': suite.dataset_type, 'scope': suite.scope,
        'manifest_sha256': _hash(raw), 'suite_evaluator_sha256': _hash(Path(__file__).read_bytes()),
        'case_count': len(reports), 'unique_page_context_count': len(page_owners),
        'review_complete': complete, 'counts': totals,
        'metrics': _metrics(totals) if complete else None,
        f'by_{dimension}': grouped,
        'unreviewed_labels': sum(report['unreviewed_labels'] for report in reports),
        'unjudged_predictions': sum(report['unjudged_predictions'] for report in reports),
        'counts_scope': 'Reviewed labels only; complete cases additionally count unmatched predictions as FP',
        'metrics_purpose': reports[0]['metrics_purpose'],
        'collection_warning_count': sum(len(report['collection_warnings']) for report in reports),
        'prediction_repetition': summarize_content_repetition(reports) if suite.kind == 'content' else None,
        'reports': reports,
    }
