"""
AccountingBench — Judge-Only Re-scoring Script
================================================
Re-runs ONLY the LLM-as-a-judge step against existing benchmark_outputs rows.
The target model is never called again — this is for cases where a task's
grading data changed after models already ran (e.g. numeric_tolerance was
missing and has since been set), so only the score needs to be recomputed
from the already-stored final_answer.

Usage
-----
# Re-judge every model's existing output on specific tasks
python -m backend.rejudge --question-ids "11830492_0007:11830492_0014" --dry-run
python -m backend.rejudge --question-ids "11830492_0007:11830492_0014"

# Restrict to specific model(s)
python -m backend.rejudge --question-ids "11830492_0007:11830492_0014" --models "gpt-5.4"

# By BenchmarkTask.id instead of question_id
python -m backend.rejudge --task-ids "19,42,100:110"

Flags
-----
--question-ids   Filter tasks by question_id. Same syntax as rerun_model.py:
                 exact ('11830492_0007'), prefix ('11830492'), or range
                 ('11830492_0007:11830492_0014').
--task-ids       Filter tasks by BenchmarkTask.id (integer primary key).
                 Same syntax as rerun_model.py: exact or range ('19,100:110').
--models         Optional. Comma-separated model name(s). Restricts rejudging
                 to these models' outputs. If omitted, every model with an
                 existing judge-scored output on the selected tasks is rejudged.
--max-workers    Max parallel judge calls (default: 10).
--sequential     Run one output at a time.
--dry-run        Print what would be rejudged without calling the judge or
                 writing to the DB.

How it works
------------
1. Queries benchmark_tasks matching --question-ids / --task-ids.
2. For each task, queries benchmark_outputs with evaluation_method == "judge"
   (sc_mc_formula outputs are never rejudged — they don't use the judge),
   optionally filtered to --models.
3. For each output, calls pipeline.call_judge() with the task's CURRENT
   grading fields (gold_answer, grading_criteria, acceptable_variants,
   numeric_tolerance) against the output's already-stored final_answer.
4. Overwrites judge_score_percent / judge_confidence / final_score_percent /
   judge_token_input / judge_token_output / evaluation_notes / evaluated_at_utc
   on the same row. No new rows are created, and model_answer_*/final_answer
   are never touched.
"""

import argparse
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent  # accountingbench/ root
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv
load_dotenv(dotenv_path=_ROOT / ".env", override=False)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("rejudge")

# ── Imports (after env is loaded) ─────────────────────────────────────────────
from datetime import datetime, timezone

from backend.database import SessionLocal
from backend.models   import BenchmarkTask, BenchmarkOutput
from backend.batch_utils import setup_error_log
from backend.processing.pipeline import call_judge, parse_tolerance
from backend.rerun_model import (
    _parse_question_ids, _build_qid_filter,
    _parse_task_ids, _build_task_id_filter,
)


def rejudge_output(task_id: int, question_id: str, model_name: str,
                    dry_run: bool) -> dict:
    """Re-runs call_judge() for one existing BenchmarkOutput row and writes
    the result back in place."""
    result = {
        "question_id": question_id, "model_name": model_name,
        "status": "unknown", "old_score": None, "new_score": None, "error": None,
    }

    db = SessionLocal()
    try:
        task = db.query(BenchmarkTask).filter_by(id=task_id).first()
        output = db.query(BenchmarkOutput).filter_by(
            task_id=task_id, model_name=model_name
        ).first()
        if task is None or output is None:
            result["status"] = "error"
            result["error"]  = "task or output not found"
            return result

        result["old_score"] = output.judge_score_percent

        if dry_run:
            result["status"] = "dry-run"
            return result

        judge_score_percent, judge_conf, jnotes, judge_tok_in, judge_tok_out = call_judge(
            task.prompt, output.final_answer, task.gold_answer,
            grading_criteria=task.grading_criteria,
            acceptable_variants=task.acceptable_variants,
            numeric_tol=parse_tolerance(task.numeric_tolerance),
            context={
                "run_id":  output.run_id,
                "task_id": task_id,
                "model":   model_name,
            },
        )

        output.judge_score_percent = judge_score_percent
        output.judge_confidence    = judge_conf
        output.final_score_percent = judge_score_percent
        output.judge_token_input   = judge_tok_in
        output.judge_token_output  = judge_tok_out
        output.evaluation_notes    = f"{output.evaluation_notes or ''}; rejudged. {jnotes}".strip("; ")
        output.evaluated_at_utc    = datetime.now(timezone.utc)
        db.commit()

        result["status"]    = "done"
        result["new_score"] = judge_score_percent

    except Exception as e:
        logger.error(f"[ERROR] {question_id} / {model_name}: {e}", exc_info=True)
        result["status"] = "error"
        result["error"]  = str(e)
    finally:
        db.close()

    return result


def log_summary(results: list) -> None:
    done    = [r for r in results if r["status"] == "done"]
    dry_run = [r for r in results if r["status"] == "dry-run"]
    errors  = [r for r in results if r["status"] == "error"]

    logger.info("")
    logger.info("=" * 60)
    logger.info("REJUDGE SUMMARY")
    logger.info("=" * 60)
    logger.info(f"  Total:   {len(results)}")
    logger.info(f"  Done:    {len(done)}")
    logger.info(f"  Dry-run: {len(dry_run)}")
    logger.info(f"  Errors:  {len(errors)}")

    for r in dry_run:
        logger.info(f"  [DRY-RUN] {r['question_id']} / {r['model_name']}  (current score: {r['old_score']})")

    for r in done:
        logger.info(f"  {r['question_id']} / {r['model_name']}  {r['old_score']} → {r['new_score']}")

    if errors:
        logger.info("")
        logger.info("Errors:")
        for r in errors:
            logger.info(f"  {r['question_id']} / {r['model_name']}: {r['error']}")

    logger.info("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Re-run only the LLM judge against existing benchmark_outputs rows."
    )
    parser.add_argument("--question-ids", default=None, dest="question_ids",
        help="Filter tasks by question_id (exact / prefix / range, same syntax as rerun_model.py).")
    parser.add_argument("--task-ids", default=None, dest="task_ids",
        help="Filter tasks by BenchmarkTask.id (exact / range, same syntax as rerun_model.py).")
    parser.add_argument("--models", default=None,
        help="Comma-separated model name(s) to restrict rejudging to. Default: all models.")
    parser.add_argument("--max-workers", type=int, default=10, dest="max_workers",
        help="Max parallel judge calls (default: 10).")
    parser.add_argument("--sequential", action="store_true",
        help="Run one output at a time.")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run",
        help="Print what would be rejudged without calling the judge or writing to the DB.")
    args = parser.parse_args()
    setup_error_log("rejudge")

    filter_qids     = _parse_question_ids(args.question_ids)
    filter_task_ids = _parse_task_ids(args.task_ids)
    filter_models   = [m.strip() for m in args.models.split(",")] if args.models else None

    if not filter_qids and not filter_task_ids:
        logger.error("No tasks specified. Use --question-ids or --task-ids.")
        sys.exit(1)

    db = SessionLocal()
    try:
        query = db.query(BenchmarkTask)
        if filter_qids:
            query = query.filter(_build_qid_filter(filter_qids))
        if filter_task_ids:
            query = query.filter(_build_task_id_filter(filter_task_ids))
        tasks = query.all()
        logger.info(f"Found {len(tasks)} task(s) matching filters.")

        work_items = []  # (task_id, question_id, model_name)
        for task in tasks:
            outputs_query = db.query(BenchmarkOutput).filter_by(
                task_id=task.id, evaluation_method="judge"
            )
            if filter_models:
                outputs_query = outputs_query.filter(BenchmarkOutput.model_name.in_(filter_models))
            for output in outputs_query.all():
                work_items.append((task.id, task.question_id, output.model_name))
    finally:
        db.close()

    logger.info(f"Outputs to rejudge: {len(work_items)}")
    if not work_items:
        logger.info("Nothing to do.")
        return

    results = []
    if args.dry_run or args.sequential or len(work_items) == 1:
        for i, (tid, qid, model) in enumerate(work_items, 1):
            logger.info(f"[{i}/{len(work_items)}] {qid} / {model}")
            results.append(rejudge_output(tid, qid, model, args.dry_run))
    else:
        max_workers = min(args.max_workers, len(work_items))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(rejudge_output, tid, qid, model, args.dry_run): (qid, model)
                for tid, qid, model in work_items
            }
            for future in as_completed(futures):
                results.append(future.result())

    log_summary(results)


if __name__ == "__main__":
    main()
