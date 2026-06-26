"""pytest configuration: makes ``tests/_fixtures.py`` importable."""
from __future__ import annotations

import sys
from pathlib import Path

# Add the tests/ directory to sys.path so ``from _fixtures import …`` works.
_TESTS_DIR = Path(__file__).resolve().parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))