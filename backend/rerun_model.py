"""
AccountingBench — Model Re-run Script
======================================
Runs one or more NEW models against ALL tasks already in the database.
Existing benchmark_outputs for the requested model(s) are skipped.
Results are written to benchmark_runs + benchmark_outputs exactly as if
the model had been included in the original batch run.

Usage
-----
# Run a single new model on all tasks
python -m backend.rerun_model --models "Kimi-K2.6"

# Run multiple new models
python -m backend.rerun_model --models "Kimi-K2.6,gpt-5.5"

# Limit parallelism (recommended: floor(50 / num_models))
python -m backend.rerun_model --models "Kimi-K2.6" --max-workers 15

# Dry run — show what would be processed without writing anything
python -m backend.rerun_model --models "Kimi-K2.6" --dry-run

# Run sequentially (safest for large datasets)
python -m backend.rerun_model --models "Kimi-K2.6" --sequential

Flags
-----
--models        Required. Comma-separated model name(s) from MODEL_REGISTRY_JSON.
--max-workers   Max parallel tasks (default: 10).
--sequential    Run one task at a time.
--dry-run       Print plan without writing to DB or calling any APIs.
--user          User ID for created submissions (default: batch_admin).

How it works
------------
1. Queries ALL benchmark_tasks from the database.
2. For each task, checks benchmark_outputs for existing rows matching the
   requested model(s). Tasks where ALL requested models already have outputs
   are skipped entirely.
3. For tasks that need running, creates a new Submission row.
4. Temporarily sets OPENAI_MODEL_LIST in os.environ to only the requested
   model(s), then calls run_pipeline(submission.id) — which reads that env
   var and runs only those models.
5. After each pipeline call, restores OPENAI_MODEL_LIST to its original value.

The pipeline itself is unchanged. Outputs are linked to the existing task via
submission.task_id → benchmark_outputs.task_id, exactly as in a normal run.
"""

import argparse
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
_ROOT     = Path(__file__).resolve().parent.parent  # accountingbench/ root
_BACKEND  = Path(__file__).resolve().parent          # accountingbench/backend/
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv
_ENV_PATH = _ROOT / ".env"
load_dotenv(dotenv_path=_ENV_PATH, override=False)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("rerun_model")

# ── Imports (after env is loaded) ─────────────────────────────────────────────
from backend.database import SessionLocal
from backend.models   import BenchmarkTask, BenchmarkOutput, Submission
from backend.processing.pipeline import run_pipeline
from backend.batch_utils import (
    ensure_batch_user,
    create_submission,
    get_existing_model_outputs,
    log_summary,
    BATCH_USER_ID,
)

# ── Helpers ───────────────────────────────────────────────────────────────────
ORIG_MODEL_LIST = os.environ.get("OPENAI_MODEL_LIST", "")


def process_task(task_id: int, task_qid: str, models_needed: list[str],
                 user_id: str, dry_run: bool,
                 index: int = 0, total: int = 0) -> dict:
    """
    Creates a submission for one task and runs only the needed models.
    Temporarily overrides OPENAI_MODEL_LIST so the pipeline only calls
    the models that are missing for this task.
    """
    prefix = f"[{index}/{total}]"
    result = {"question_id": task_qid, "status": "unknown",
              "submission_id": None, "models": models_needed, "error": None}

    if dry_run:
        logger.info(f"{prefix} [DRY-RUN] Would run {models_needed} on task {task_qid}")
        result["status"] = "dry-run"
        return result

    db = SessionLocal()
    try:
        task = db.query(BenchmarkTask).filter_by(id=task_id).first()
        if not task:
            raise ValueError(f"Task {task_id} not found in DB")

        sub = create_submission(db, task, user_id)
        result["submission_id"] = sub.id
        logger.info(f"{prefix} ── Task: {task_qid} ──────────────────────────────")
        logger.info(f"{prefix} [RUN] {task_qid} → submission {sub.id} — models: {models_needed}")

        # Close this session before pipeline opens its own
        db.close()
        db = None

        # Override model list so pipeline only runs the needed models
        os.environ["OPENAI_MODEL_LIST"] = ",".join(models_needed)
        try:
            run_pipeline(sub.id)
        finally:
            # Always restore original model list
            os.environ["OPENAI_MODEL_LIST"] = ORIG_MODEL_LIST

        logger.info(f"{prefix} [DONE] {task_qid} → submission {sub.id} — complete.")
        result["status"] = "done"

    except Exception as e:
        logger.error(f"{prefix} [ERROR] {task_qid}: {e}", exc_info=True)
        result["status"] = "error"
        result["error"]  = str(e)
    finally:
        if db:
            db.close()

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Run new model(s) against all tasks already in the database."
    )
    parser.add_argument(
        "--models", required=True,
        help="Comma-separated model name(s) to run, e.g. 'Kimi-K2.6' or 'Kimi-K2.6,gpt-5.5'",
    )
    parser.add_argument(
        "--max-workers", type=int, default=10,
        help="Max parallel tasks (default: 10). Rule of thumb: floor(50 / num_models).",
    )
    parser.add_argument(
        "--sequential", action="store_true",
        help="Run one task at a time (safest for large datasets).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would run without writing to DB or calling APIs.",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Only process the first N tasks (useful for testing, e.g. --limit 1).",
    )
    parser.add_argument(
        "--user", default=os.environ.get("BATCH_USER_ID", "batch_admin"),
        help="User ID for created submissions (default: batch_admin).",
    )
    args = parser.parse_args()

    # Parse requested models
    requested_models = [m.strip() for m in args.models.split(",") if m.strip()]
    if not requested_models:
        logger.error("--models must contain at least one model name.")
        sys.exit(1)

    logger.info(f"Models requested:  {requested_models}")
    logger.info(f"Max workers:       {args.max_workers}")
    logger.info(f"Sequential:        {args.sequential}")
    logger.info(f"Dry run:           {args.dry_run}")
    logger.info(f"User:              {args.user}")

    # ── Load all tasks from DB ────────────────────────────────────────────────
    db = SessionLocal()
    try:
        all_tasks = db.query(BenchmarkTask).all()
        logger.info(f"Found {len(all_tasks)} tasks in database.")

        # For each task, determine which requested models are still missing
        work_items = []  # list of (task_id, task_qid, models_needed)
        skipped = 0

        for task in all_tasks:
            existing = get_existing_model_outputs(db, task.id, requested_models)
            missing  = [m for m in requested_models if m not in existing]
            if not missing:
                skipped += 1
                continue
            work_items.append((task.id, task.question_id or str(task.id), missing))

    finally:
        db.close()

    logger.info(f"Tasks to process:  {len(work_items)}")
    logger.info(f"Tasks skipped:     {skipped} (outputs already exist for all requested models)")

    if args.limit:
        work_items = work_items[:args.limit]
        logger.info(f"Limiting to first:  {len(work_items)} task(s) (--limit {args.limit})")

    if not work_items:
        logger.info("Nothing to do — all requested models already have outputs for all tasks.")
        return

    if args.dry_run:
        for i, (tid, qid, models) in enumerate(work_items, 1):
            logger.info(f"  [{i}/{len(work_items)}] {qid} — would run: {models}")
        logger.info("Dry run complete. No changes made.")
        return

    # ── Run tasks ─────────────────────────────────────────────────────────────
    results   = []
    total     = len(work_items)

    if args.sequential or total == 1:
        logger.info(f"Running {total} task(s) sequentially...")
        for i, (tid, qid, models) in enumerate(work_items, 1):
            logger.info(f"\n{'─' * 60}")
            logger.info(f"  Task {i}/{total}: {qid}")
            logger.info(f"{'─' * 60}")
            results.append(process_task(tid, qid, models, args.user, args.dry_run, i, total))
    else:
        max_workers = min(args.max_workers, total)
        logger.info(f"Running {total} task(s) in parallel (max_workers={max_workers})...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(process_task, tid, qid, models,
                                args.user, args.dry_run, i + 1, total): qid
                for i, (tid, qid, models) in enumerate(work_items)
            }
            for future in as_completed(futures):
                results.append(future.result())

    log_summary(results, title="RERUN SUMMARY")


if __name__ == "__main__":
    main()
