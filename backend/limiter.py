"""
AccountingBench — Rate Limiter
==============================
Shared slowapi Limiter instance imported by main.py (middleware + exception
handler) and individual router files (per-endpoint decorators).

Limits are per IP address. Adjust the constants below to tune thresholds.
For production with multiple Uvicorn workers, swap the default in-memory
storage for Redis:

    from slowapi import Limiter
    from slowapi.util import get_remote_address
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[LIMIT_DEFAULT],
        storage_uri="redis://localhost:6379",
    )
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# ── Thresholds ────────────────────────────────────────────────────────────────
LIMIT_DEFAULT = "60/minute"   # global fallback for every endpoint
LIMIT_SUBMIT  = "5/minute"    # POST /submissions/prepare  (expensive: DB + Stripe + pipeline)
LIMIT_PAYMENT = "10/minute"   # POST /submissions/{id}/confirm-payment

limiter = Limiter(key_func=get_remote_address, default_limits=[LIMIT_DEFAULT])
