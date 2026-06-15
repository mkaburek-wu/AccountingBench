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

# Filter by category
python -m backend.rerun_model --models "Kimi-K2.6" --category "Tax"
python -m backend.rerun_model --models "Kimi-K2.6" --category "Tax,Financial Accounting"

# Filter by task type
python -m backend.rerun_model --models "Kimi-K2.6" --task-type "calculation"

# Filter by answer type
python -m backend.rerun_model --models "Kimi-K2.6" --answer-type "single_choice,multi_choice"

# Filter by education level
python -m backend.rerun_model --models "Kimi-K2.6" --education-level "University Master's"

# Filter by regulatory framework
python -m backend.rerun_model --models "Kimi-K2.6" --regulatory-framework "Austrian Tax Law"

# Run only specific tasks by question_id
python -m backend.rerun_model --models "Kimi-K2.6" --question-ids "q_0001,q_0042"

# Combine filters (all conditions must match)
python -m backend.rerun_model --models "Kimi-K2.6" --category "Tax" --task-type "calculation" --dry-run

Flags
-----
--models                Optional. Comma-separated model name(s) from MODEL_REGISTRY_JSON.
                        If omitted, OPENAI_MODEL_LIST from .env is used.
--max-workers           Max parallel tasks (default: 10).
--sequential            Run one task at a time.
--dry-run               Print plan without writing to DB or calling any APIs.
--user                  User ID for created submissions (default: batch_admin).
--category              Filter by category. Comma-separated.
                        Values: Tax | Financial Accounting | Management Accounting
--task-type             Filter by task_type. Comma-separated.
                        Values: interpretation_of_law | calculation | journal_entry
--answer-type           Filter by answer_type. Comma-separated.
                        Values: single_choice | multi_choice | open_text | open_numeric | journal_entry
--education-level       Filter by education_level. Comma-separated.
                        Values: Professional Examinations | University Master's | Secondary Vocational
--regulatory-framework  Filter by regulatory_framework. Comma-separated.
                        Values: Austrian Tax Law | IFRS | National GAAP |
                                Mixed Accounting Framework | Mixed: Accounting + Tax
--question-ids          Run only these specific tasks. Comma-separated question_id values.

How it works
------------
1. Queries ALL benchmark_tasks from the database.
2. For each task, checks benchmark_outputs for existing rows matching the
   requested model(s). Tasks where ALL requested models already have outputs
   are skipped entirely.
3. For tasks that need running, creates a new Submission row.
4. Calls run_pipeline(submission.id) — which reads OPENAI_MODEL_LIST from the
   environment to determine which models to run. OPENAI_MODEL_LIST is set once
   at startup (from --models or from OPENAI_MODEL_LIST in .env) before any
   threads are started, so it is never mutated during parallel execution.

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
from sqlalchemy import func
from backend.database import SessionLocal
from backend.models   import BenchmarkTask
from backend.processing.pipeline import run_pipeline, InsufficientBalanceError, IncompleteRunError
from backend.batch_utils import (
    ensure_batch_user,
    create_submission,
    get_existing_model_outputs,
    log_summary,
    setup_error_log,
    test_endpoints,
    check_field_consistency,
    BATCH_USER_ID,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

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

        pipeline_status = run_pipeline(sub.id)
        if pipeline_status == "error":
            logger.warning(f"{prefix} [FAIL] {task_qid} → submission {sub.id} — all models failed.")
            result["status"] = "error"
            result["error"]  = "All models failed"
        else:
            logger.info(f"{prefix} [DONE] {task_qid} → submission {sub.id} — complete.")
            result["status"] = "done"

    except (InsufficientBalanceError, IncompleteRunError):
        if db:
            db.close()
        raise  # propagate to main loop
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
        "--models", required=False, default=None,
        help=(
            "Comma-separated model name(s) to run, e.g. 'Kimi-K2.6' or 'Kimi-K2.6,gpt-5.5'. "
            "Overrides OPENAI_MODEL_LIST from .env. If omitted, OPENAI_MODEL_LIST from .env is used."
        ),
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
    parser.add_argument(
        "--category", default=None,
        help=(
            "Filter tasks by category. Comma-separated. "
            "Values: Tax | Financial Accounting | Management Accounting"
        ),
    )
    parser.add_argument(
        "--task-type", default=None,
        dest="task_type",
        help=(
            "Filter by task_type. Comma-separated. "
            "Values: interpretation_of_law | calculation | journal_entry"
        ),
    )
    parser.add_argument(
        "--answer-type", default=None,
        dest="answer_type",
        help=(
            "Filter by answer_type. Comma-separated. "
            "Values: single_choice | multi_choice | open_text | open_numeric | journal_entry"
        ),
    )
    parser.add_argument(
        "--education-level", default=None,
        dest="education_level",
        help=(
            "Filter by education_level. Comma-separated. "
            "Values: Professional Examinations | University Master's | Secondary Vocational"
        ),
    )
    parser.add_argument(
        "--regulatory-framework", default=None,
        dest="regulatory_framework",
        help=(
            "Filter by regulatory_framework. Comma-separated. "
            "Values: Austrian Tax Law | IFRS | National GAAP | "
            "Mixed Accounting Framework | Mixed: Accounting + Tax"
        ),
    )
    parser.add_argument(
        "--question-ids", default=None,
        dest="question_ids",
        help="Run only specific tasks. Comma-separated question_id values, e.g. 'q_0001,q_0042'.",
    )
    args = parser.parse_args()
    setup_error_log("rerun_model")

    # Resolve model list: --models overrides OPENAI_MODEL_LIST from .env
    if args.models:
        requested_models = [m.strip() for m in args.models.split(",") if m.strip()]
    else:
        env_list = os.environ.get("OPENAI_MODEL_LIST", "")
        requested_models = [m.strip() for m in env_list.split(",") if m.strip()]

    if not requested_models:
        logger.error("No models specified. Use --models or set OPENAI_MODEL_LIST in .env")
        sys.exit(1)

    # Set once before any threads start — pipeline reads this value, never written again
    os.environ["OPENAI_MODEL_LIST"] = ",".join(requested_models)

    # Parse filter values (split comma-separated strings into lists)
    def _split(val):
        return [v.strip() for v in val.split(",") if v.strip()] if val else None

    filter_category    = _split(args.category)
    filter_task_type   = _split(args.task_type)
    filter_answer_type = _split(args.answer_type)
    filter_edu_level   = _split(args.education_level)
    filter_reg_fw      = _split(args.regulatory_framework)
    filter_qids        = _split(args.question_ids)

    logger.info(f"Models requested:        {requested_models}")
    logger.info(f"Max workers:             {args.max_workers}")
    logger.info(f"Sequential:              {args.sequential}")
    logger.info(f"Dry run:                 {args.dry_run}")
    logger.info(f"User:                    {args.user}")
    if filter_category:    logger.info(f"Filter category:         {filter_category}")
    if filter_task_type:   logger.info(f"Filter task_type:        {filter_task_type}")
    if filter_answer_type: logger.info(f"Filter answer_type:      {filter_answer_type}")
    if filter_edu_level:   logger.info(f"Filter education_level:  {filter_edu_level}")
    if filter_reg_fw:      logger.info(f"Filter reg. framework:   {filter_reg_fw}")
    if filter_qids:        logger.info(f"Filter question_ids:     {filter_qids}")

    # ── Load tasks from DB (with optional filters) ────────────────────────────
    db = SessionLocal()
    try:
        query = db.query(BenchmarkTask)

        # DB stores values as lowercase_underscore (e.g. "professional_examinations").
        # Normalize filter values the same way so "Professional Examinations" also matches.
        def _norm(v: str) -> str:
            return v.lower().replace(" ", "_").replace("-", "_")

        if filter_category:
            query = query.filter(func.lower(BenchmarkTask.category).in_([_norm(v) for v in filter_category]))
        if filter_task_type:
            query = query.filter(func.lower(BenchmarkTask.task_type).in_([_norm(v) for v in filter_task_type]))
        if filter_answer_type:
            query = query.filter(func.lower(BenchmarkTask.answer_type).in_([_norm(v) for v in filter_answer_type]))
        if filter_edu_level:
            query = query.filter(func.lower(BenchmarkTask.education_level).in_([_norm(v) for v in filter_edu_level]))
        if filter_reg_fw:
            query = query.filter(func.lower(BenchmarkTask.regulatory_framework).in_([_norm(v) for v in filter_reg_fw]))
        if filter_qids:
            query = query.filter(BenchmarkTask.question_id.in_(filter_qids))

        all_tasks = query.all()
        logger.info(f"Found {len(all_tasks)} tasks matching filters.")

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

        # Field consistency check — re-query only the tasks that would run
        task_ids = [tid for tid, _, _ in work_items]
        if task_ids:
            db_check = SessionLocal()
            try:
                tasks_to_check = db_check.query(BenchmarkTask).filter(
                    BenchmarkTask.id.in_(task_ids)
                ).all()
                check_field_consistency([
                    {
                        "question_id":      t.question_id,
                        "answer_type":      t.answer_type,
                        "grading_criteria": t.grading_criteria,
                        "numeric_tolerance": t.numeric_tolerance,
                    }
                    for t in tasks_to_check
                ])
            finally:
                db_check.close()

        test_endpoints(requested_models)
        return

    # ── Run tasks ─────────────────────────────────────────────────────────────
    results    = []
    total      = len(work_items)
    stop_error: Exception | None = None

    if args.sequential or total == 1:
        logger.info(f"Running {total} task(s) sequentially...")
        for i, (tid, qid, models) in enumerate(work_items, 1):
            logger.info(f"\n{'─' * 60}")
            logger.info(f"  Task {i}/{total}: {qid}")
            logger.info(f"{'─' * 60}")
            try:
                results.append(process_task(tid, qid, models, args.user, args.dry_run, i, total))
            except (InsufficientBalanceError, IncompleteRunError) as e:
                stop_error = e
                break
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
                try:
                    results.append(future.result())
                except (InsufficientBalanceError, IncompleteRunError) as e:
                    if stop_error is None:
                        stop_error = e
                        for f in futures:
                            f.cancel()  # cancel queued (not yet started) tasks

    log_summary(results, title="RERUN SUMMARY")

    if stop_error is not None:
        if isinstance(stop_error, InsufficientBalanceError):
            logger.error(f"STOPPED — insufficient balance: {stop_error}")
            logger.error("Top up your API account balance, then resume:")
            logger.error("  python -m backend.rerun_model   (picks up all missing model outputs)")
        else:
            logger.error(f"STOPPED — incomplete task: {stop_error}")
            logger.error("Fix the failing model config, then resume:")
            logger.error("  python -m backend.rerun_model   (picks up all missing model outputs)")
        sys.exit(1)


if __name__ == "__main__":
    main()
