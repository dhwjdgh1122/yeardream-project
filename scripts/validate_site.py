"""Capture bounded site inputs, then evaluate reviewed saved feature labels."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.evaluation import capture_site, evaluate_capture


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    capture = commands.add_parser('capture', help='Collect a new bounded snapshot run')
    capture.add_argument('url')
    capture.add_argument('--output', type=Path, required=True)
    capture.add_argument('--mode', choices=['static', 'browser'], default='static')
    capture.add_argument('--max-depth', type=int, default=0)
    capture.add_argument('--total-timeout-sec', type=float, default=60)
    capture.add_argument('--render-wait-ms', type=int, default=500)
    evaluate = commands.add_parser('evaluate', help='Replay saved HTML without network access')
    evaluate.add_argument('directory', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'capture':
            data = capture_site(args.url, args.output, mode=args.mode, max_depth=args.max_depth,
                                total_timeout_sec=args.total_timeout_sec, render_wait_ms=args.render_wait_ms)
            print(json.dumps({'documents': len(data['documents']), 'predictions': len(data['predictions']),
                              'content_candidates': len(data['content_candidates']),
                              'warnings': len(data['warnings']), 'output': str(args.output)}))
            return 0 if any('file' in doc for doc in data['documents']) else 2
        report = evaluate_capture(args.directory)
        output = args.directory / 'report.json'
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps({key: report[key] for key in ('review_complete', 'prediction_count', 'content_candidate_count',
                         'unreviewed_labels', 'unjudged_predictions', 'counts', 'metrics')}))
        return 0
    except (ValueError, OSError, RuntimeError, KeyError) as error:
        print(f'Validation failed: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(run())
