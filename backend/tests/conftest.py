"""
Pytest configuration for the AccountingBench test suite.

Puts the project root on sys.path so `backend.*` imports resolve regardless of
where pytest is invoked from.

These tests cover **pure functions only** — scoring, parsing, and the
results.js export helpers. They never touch the database and never call a model
API, so the suite is fast and safe to run at any time.

Run from the project root:
    python -m pytest backend/tests -v
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent  # accountingbench/ root
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
