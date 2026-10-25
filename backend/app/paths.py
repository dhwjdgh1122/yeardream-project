"""Keep bundled read-only assets separate from user-visible result files."""

import sys
import os
from pathlib import Path


def history_database_path():
    """Keep mutable history outside the application and synchronized source tree."""
    base = Path(os.environ['LOCALAPPDATA']) if os.environ.get('LOCALAPPDATA') else Path.home() / '.local' / 'share'
    return base / 'YearDream' / 'history.sqlite3'


def resource_root():
    return Path(__file__).resolve().parents[2]


def output_root():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return resource_root()
