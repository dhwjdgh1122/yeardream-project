"""Re-evaluate pinned saved cases and write a new aggregate report, offline."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.validation_suite import evaluate_suite


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError('Output already exists; choose a new report path')
        report = evaluate_suite(args.manifest)
        with args.output.open('x', encoding='utf-8', newline='\n') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
        print(json.dumps({key: report[key] for key in ('case_count', 'review_complete', 'counts', 'metrics',
                                                      'unreviewed_labels', 'unjudged_predictions')}))
        return 0
    except (ValueError, OSError, RuntimeError, KeyError) as error:
        print(f'Suite evaluation failed: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(run())
