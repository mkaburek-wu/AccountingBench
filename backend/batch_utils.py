"""
AccountingBench — Shared Batch Utilities
==========================================
Shared helpers used by both batch_run.py and rerun_model.py.
Do not add script-specific logic here.
"""

import logging
import os
from datetime import datetime, timezone

from backend.database import SessionLocal
from backend.models   import BenchmarkTask, BenchmarkOutput, Submission, User

logger = logging.getLogger("batch_utils")

# ── Environment ───────────────────────────────────────────────────────────────
BATCH_USER_ID    = os.environ.get("BATCH_USER_ID",    "batch_admin")
BATCH_USER_EMAIL = os.environ.get("BATCH_USER_EMAIL", "batch@accountingbench.local")


def ensure_batch_user(db) -> None:
    """Create the batch user row in the users table if it doesn't exist yet."""
    existing = db.query(User).filter_by(id=BATCH_USER_ID).first()
    if not existing:
        db.add(User(
            id         = BATCH_USER_ID,
            email      = BATCH_USER_EMAIL,
            first_name = "Batch",
            last_name  = "Runner",
        ))
        db.commit()
        logger.info(f"Created batch user: {BATCH_USER_ID}")


def create_submission(db, task: BenchmarkTask, user_id: str) -> Submission:
    """Create a new pending Submission row linked to the given task."""
    sub = Submission(
        user_id        = user_id,
        task_id        = task.id,
        status         = "pending",
        payment_status = "unpaid",
        submitted_at   = datetime.now(timezone.utc),
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    logger.info(f"  Created submission {sub.id} for task {task.question_id}")
    return sub


def get_existing_model_outputs(db, task_id: int, models: list) -> set:
    """
    Return the set of model names that already have a benchmark_output
    row for the given task_id. Used by rerun_model.py to skip completed work.
    """
    rows = (
        db.query(BenchmarkOutput.model_name)
        .filter(
            BenchmarkOutput.task_id    == task_id,
            BenchmarkOutput.model_name.in_(models),
        )
        .all()
    )
    return {r.model_name for r in rows}


def log_summary(results: list, title: str = "SUMMARY") -> None:
    """Print a standardised run summary to the logger."""
    done    = [r for r in results if r["status"] == "done"]
    skipped = [r for r in results if r["status"] == "skipped"]
    errors  = [r for r in results if r["status"] == "error"]

    logger.info("")
    logger.info("=" * 60)
    logger.info(title)
    logger.info("=" * 60)
    logger.info(f"  Total:   {len(results)}")
    logger.info(f"  Done:    {len(done)}")
    logger.info(f"  Skipped: {len(skipped)}")
    logger.info(f"  Errors:  {len(errors)}")

    if done:
        logger.info("")
        logger.info("Completed submissions:")
        for r in done:
            extra = f" — models: {r['models']}" if r.get("models") else ""
            logger.info(f"  {r['question_id']} → submission {r['submission_id']}{extra}")

    if errors:
        logger.info("")
        logger.info("Errors:")
        for r in errors:
            logger.info(f"  {r['question_id']}: {r['error']}")

    logger.info("=" * 60)
