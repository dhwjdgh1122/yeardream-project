"""Score curated synthetic content cases; these metrics are not real-site accuracy."""
import argparse
import hashlib
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.content import POLICY_VERSION, detect_content


def benchmark():
    raw = (ROOT / 'tests/fixtures/content/cases.json').read_bytes()
    dataset = json.loads(raw)
    counts = dict(tp=0, fp=0, fn=0, tn=0)
    details = []
    for case in dataset['cases']:
        predicted = {item['category'] for item in detect_content({
            'url': 'https://synthetic.example.test', 'html': '<p>' + html.escape(case['text']) + '</p>'})}
        expected = set(case['expected'])
        for category in ('GAMBLING', 'ADULT_CONTENT'):
            outcome = ('tp' if category in predicted else 'fn') if category in expected else ('fp' if category in predicted else 'tn')
            counts[outcome] += 1
        details.append(dict(id=case['id'], expected=sorted(expected), predicted=sorted(predicted),
                            passed=expected == predicted, reason=case['reason']))
    tp, fp, fn = counts['tp'], counts['fp'], counts['fn']
    return dict(scope=dataset['scope'], policy_version=POLICY_VERSION,
                dataset_sha256=hashlib.sha256(raw).hexdigest(),
                detector_sha256=hashlib.sha256((ROOT / 'backend/app/content.py').read_bytes()).hexdigest(),
                normalizer_sha256=hashlib.sha256((ROOT / 'backend/app/textnorm.py').read_bytes()).hexdigest(),
                case_count=len(details), passed_cases=sum(item['passed'] for item in details), counts=counts,
                metrics=dict(precision=tp / (tp + fp) if tp + fp else None,
                             recall=tp / (tp + fn) if tp + fn else None,
                             f1=2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None), details=details)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = benchmark()
    if args.output:
        with args.output.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
    print(json.dumps({key: value for key, value in report.items() if key != 'details'}))
