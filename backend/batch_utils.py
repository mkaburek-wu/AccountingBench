"""
AccountingBench — Shared Batch Utilities
==========================================
Shared helpers used by both batch_run.py and rerun_model.py.
Do not add script-specific logic here.
"""

import logging
import os
import re
import requests
import pandas as pd
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


def check_attached_files(raw, uploads_dir: str) -> tuple[list[str], list[str]]:
    """Check which files in an attached_files cell can be resolved on disk.
    Returns (found_paths, missing_entries) — no side effects, no logging.
    Useful for dry-run validation before a real import.
    """
    found: list[str] = []
    missing: list[str] = []
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return found, missing
    s = str(raw).strip()
    if not s:
        return found, missing

    for entry in s.split("|"):
        entry = entry.strip()
        if not entry:
            continue
        if re.match(r"^https?://", entry, re.IGNORECASE):
            found.append(entry)
            continue
        if os.path.isabs(entry) and os.path.exists(entry):
            found.append(entry)
            continue
        candidate = os.path.join(uploads_dir, entry)
        if os.path.exists(candidate):
            found.append(os.path.abspath(candidate))
            continue
        filename = os.path.basename(entry)
        candidate2 = os.path.join(uploads_dir, filename)
        if os.path.exists(candidate2):
            found.append(os.path.abspath(candidate2))
            continue
        found_path = None
        for root, _, files in os.walk(uploads_dir):
            if filename in files:
                found_path = os.path.join(root, filename)
                break
        if found_path:
            found.append(os.path.abspath(found_path))
        else:
            missing.append(entry)

    return found, missing


def resolve_attached_files(raw, uploads_dir: str) -> str | None:
    """Resolve the attached_files cell value from an Excel row to a
    pipe-separated string of absolute paths suitable for the pipeline.

    Supports:
      - Filenames only:    "document.pdf"
      - Relative paths:   "uploads/document.pdf"
      - Absolute paths:   "C:\\...\\document.pdf"  (used as-is if exists)
      - Multiple files:   "doc1.pdf | doc2.pdf"
      - URLs (http/https): passed through unchanged
      - NaN / empty:      returns None
    """
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    s = str(raw).strip()
    if not s:
        return None

    resolved = []
    for entry in s.split("|"):
        entry = entry.strip()
        if not entry:
            continue

        if re.match(r"^https?://", entry, re.IGNORECASE):
            resolved.append(entry)
            logger.info(f"    Attached file (URL): {entry}")
            continue

        if os.path.isabs(entry) and os.path.exists(entry):
            resolved.append(entry)
            logger.info(f"    Attached file (absolute): {entry}")
            continue

        candidate = os.path.join(uploads_dir, entry)
        if os.path.exists(candidate):
            resolved.append(os.path.abspath(candidate))
            logger.info(f"    Attached file found: {candidate}")
            continue

        filename = os.path.basename(entry)
        candidate2 = os.path.join(uploads_dir, filename)
        if os.path.exists(candidate2):
            resolved.append(os.path.abspath(candidate2))
            logger.info(f"    Attached file found: {candidate2}")
            continue

        found = None
        for root, _, files in os.walk(uploads_dir):
            if filename in files:
                found = os.path.join(root, filename)
                break
        if found:
            resolved.append(os.path.abspath(found))
            logger.info(f"    Attached file found (recursive search): {found}")
            continue

        logger.warning(f"    Attached file NOT found: '{entry}' (searched in {uploads_dir})")
        resolved.append(entry)

    return " | ".join(resolved) if resolved else None


def test_endpoints(models: list) -> None:
    """Probe each model's API endpoint without consuming benchmark tokens.

    Tries GET /models/{id} first; falls back to GET /models (list) for
    providers that don't expose individual model lookup (e.g. InceptionLabs).
    """
    from backend.processing.pipeline import MODEL_REGISTRY, _get_model_api_id

    logger.info("")
    logger.info("=== ENDPOINT CHECK ===")
    ok = failed = skipped = 0

    for model in models:
        cfg      = MODEL_REGISTRY.get(model) or {}
        api_type = (cfg.get("api_type") or "").strip().lower()
        base_url = (cfg.get("base_url") or "").rstrip("/")
        api_key  = cfg.get("api_key") or ""
        model_id = _get_model_api_id(model)

        if api_type == "alawyer":
            logger.info(f"  SKIP  {model}: alawyer (no /models endpoint)")
            skipped += 1
            continue
        if not base_url:
            logger.warning(f"  SKIP  {model}: no base_url configured")
            skipped += 1
            continue

        headers = {"Authorization": f"Bearer {api_key}"}
        url     = f"{base_url}/models/{model_id}"
        try:
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                logger.info(f"  OK    {model}  →  {model_id}")
                ok += 1
            elif resp.status_code == 404:
                # Fall back to listing all models for providers that don't
                # support individual model lookup.
                list_resp = requests.get(f"{base_url}/models", headers=headers, timeout=10)
                if list_resp.status_code == 200:
                    listed_ids = [m.get("id") for m in (list_resp.json().get("data") or [])]
                    if model_id in listed_ids:
                        logger.info(f"  OK    {model}  →  {model_id}  (found via /models list)")
                        ok += 1
                    else:
                        logger.error(f"  FAIL  {model}  →  {model_id}  (not found in /models list)")
                        failed += 1
                else:
                    logger.error(f"  FAIL  {model}  →  {model_id}  (404 — model not found)")
                    failed += 1
            elif resp.status_code == 401:
                logger.error(f"  FAIL  {model}  →  {model_id}  (401 — unauthorized, check API key)")
                failed += 1
            else:
                logger.warning(f"  WARN  {model}  →  {model_id}  (HTTP {resp.status_code})")
                failed += 1
        except Exception as e:
            logger.error(f"  FAIL  {model}  →  {model_id}  (connection error: {e})")
            failed += 1

    logger.info(f"=== {ok} OK  |  {failed} failed  |  {skipped} skipped ===")
    logger.info("")
