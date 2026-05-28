"""
AccountingBench — Central configuration
========================================
All values read from environment variables (set in .env at the project root).
Import this module instead of calling os.environ directly for shared constants.
"""

import os

APP_VERSION         = os.environ.get("APP_VERSION",         "1.0.0")
DEFAULT_PRICE_CENTS = int(os.environ.get("DEFAULT_PRICE_CENTS", "5000"))
DEFAULT_CURRENCY    = os.environ.get("DEFAULT_CURRENCY",    "eur")
