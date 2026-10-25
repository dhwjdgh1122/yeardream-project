"""Export all saved content text blocks for manual review; never infer answers."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.app.review_inventory import export_content_inventory


def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        data = export_content_inventory(args.directory, args.output)
        print(json.dumps({key: data[key] for key in ('block_count', 'category_pair_count',
                                                   'reviewed_category_pairs', 'unreviewed_category_pairs')}))
        return 0
    except (ValueError, OSError, RuntimeError, KeyError) as error:
        print(f'Inventory failed: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(run())
