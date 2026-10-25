"""Keep bundled read-only assets separate from user-visible result files."""

import sys
from pathlib import Path


def resource_root():
    return Path(__file__).resolve().parents[2]


def output_root():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return resource_root()
