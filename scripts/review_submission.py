"""Initialize or export human submission reviews from saved HTML, without network access."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.review import export_submission_review, initialize_submission_review


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    initialize = commands.add_parser('init', help='Create pending submission-review.json; never overwrite')
    initialize.add_argument('directory', type=Path)
    export = commands.add_parser('export', help='Export explicit includes to a new directory with audit records')
    export.add_argument('directory', type=Path)
    export.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'init':
            data = initialize_submission_review(args.directory)
            print(json.dumps({'pending': len(data['items']), 'output': str(args.directory / 'submission-review.json')}))
        else:
            data = export_submission_review(args.directory, args.output)
            print(json.dumps({'counts': data['counts'], 'review_complete': data['review_complete'],
                              'output': str(args.output)}))
        return 0
    except (ValueError, OSError, RuntimeError, KeyError) as error:
        print(f'Review failed: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(run())
