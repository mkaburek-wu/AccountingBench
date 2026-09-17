"""
AccountingBench — Multi-Judge Comparison (DB-writing, research only)
======================================================================
Scores existing benchmark_outputs rows with one or more ALTERNATIVE judge
models and persists every judge's result — including the production judge's
existing score, copied rather than re-run — into the `judge_comparisons`
table for later analysis.

The production judge stays fixed — `pipeline.JUDGE_MODEL` ("gpt-5-mini") — and
is NEVER called again here; its existing benchmark_outputs score is copied
into judge_comparisons instead. `benchmark_outputs` / the leaderboard are
never written to by this script.

One `judge_comparisons` row exists per (benchmark_outputs row, repeat_index),
with a fixed set of columns per judge (score/confidence/tokens/notes/
timestamp) — see JUDGE_COLUMN_SLUGS in backend/models.py for the supported
judges and their column-group prefix. Adding a new judge requires a migration
(new columns) plus a new entry in that map.

Usage
-----
# Compare two alt judges against the copied gpt-5-mini scores, public tasks only
python -m backend.judge_comparison \
    --question-ids "11830492" \
    --judges "gpt-5.6-luna,claude-sonnet-5"

# Restrict to specific target model(s), 3 repeats per alt judge
python -m backend.judge_comparison \
    --task-ids "19,42,100:110" \
    --models "gpt-5.4,Kimi-K2.6" \
    --judges "gpt-5.6-luna,claude-sonnet-5" \
    --repeats 3

# Quick smoke test
python -m backend.judge_comparison --task-ids "19" --judges "gpt-5.6-luna" --sequential --dry-run

# Fill in a newly registered judge on rows that already have the others
python -m backend.judge_comparison --task-ids "19,42" --judges "DeepSeek-V4-Flash"

Flags
-----
--question-ids   Filter tasks by question_id (exact / prefix / range) — same
                 syntax as rerun_model.py / rejudge.py.
--task-ids       Filter tasks by BenchmarkTask.id (exact / range).
--judges         REQUIRED. Comma-separated judge model name(s) to run. Each
                 must be a key in models.JUDGE_COLUMN_SLUGS (other than
                 "gpt-5-mini", which is handled by the production-copy step
                 and may not be passed here).
--models         Optional. Comma-separated target model name(s) whose outputs
                 are judged. Default: every model with a judge-scored output
                 on the selected tasks.
--repeats        judge_comparisons rows (repeat_index 1..N) to produce per
                 output (default 1). >1 lets you measure judge
                 self-consistency at temperature 0.
--include-private  Include is_public = 0 tasks (default: public only,
                 matching what the site reports).
--skip-production-copy  Skip copying the gpt-5-mini score onto row 1 (use on
                 reruns where it's already been copied).
--overwrite      Re-fill a judge's columns even if already non-null. Default:
                 skip cells that are already populated (idempotent reruns).
--max-workers    Max parallel judge calls (default 10).
--sequential     Run one judge call at a time.
--dry-run        List the work without calling the judge or writing to the DB.
"""

import argparse
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent  # AccountingBench/ root
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
logger = logging.getLogger("judge_comparison")

# ── Imports (after env is loaded) ─────────────────────────────────────────────
from backend.database import SessionLocal
from backend.models   import BenchmarkTask, BenchmarkOutput, JudgeComparison, JUDGE_COLUMN_SLUGS
from backend.batch_utils import setup_error_log
from backend.processing import pipeline
from backend.processing.pipeline import call_judge, parse_tolerance
from backend.rerun_model import (
    _parse_question_ids, _build_qid_filter,
    _parse_task_ids, _build_task_id_filter,
)


def _get_or_create_row(db, output: BenchmarkOutput, repeat_index: int) -> JudgeComparison:
    row = db.query(JudgeComparison).filter_by(
        output_id=output.id, repeat_index=repeat_index
    ).first()
    if row is None:
        row = JudgeComparison(
            task_id=output.task_id, output_id=output.id,
            model_name=output.model_name, repeat_index=repeat_index,
        )
        db.add(row)
        db.flush()
    return row


def copy_production_score(row: JudgeComparison, output: BenchmarkOutput, overwrite: bool) -> bool:
    """Copy the already-stored gpt-5-mini score onto `row`. No API call. Only
    meaningful on repeat_index 1 — the production score is a single stored
    value, not something repeats measure variance on."""
    if row.repeat_index != 1:
        return False
    if row.judge_gpt5mini_score_percent is not None and not overwrite:
        return False
    row.judge_gpt5mini_score_percent = output.judge_score_percent
    row.judge_gpt5mini_confidence    = output.judge_confidence
    row.judge_gpt5mini_token_input   = output.judge_token_input
    row.judge_gpt5mini_token_output  = output.judge_token_output
    row.judge_gpt5mini_notes         = output.evaluation_notes
    row.judge_gpt5mini_evaluated_at  = output.evaluated_at_utc
    return True


def judge_cell(task_id: int, output_id: int, repeat_index: int, judge_model: str,
                dry_run: bool) -> dict:
    """Call call_judge() for one (output, repeat, judge) cell and write the
    result into that judge's column group on the matching judge_comparisons row."""
    slug = JUDGE_COLUMN_SLUGS[judge_model]
    result = {
        "task_id": task_id, "output_id": output_id, "repeat_index": repeat_index,
        "judge_model": judge_model, "status": "unknown", "score": None, "error": None,
    }

    db = SessionLocal()
    try:
        task   = db.query(BenchmarkTask).filter_by(id=task_id).first()
        output = db.query(BenchmarkOutput).filter_by(id=output_id).first()
        if task is None or output is None:
            result["status"] = "error"
            result["error"]  = "task or output not found"
            return result

        if dry_run:
            result["status"] = "dry-run"
            return result

        score, conf, notes, tok_in, tok_out = call_judge(
            task.prompt, output.final_answer, task.gold_answer,
            grading_criteria=task.grading_criteria,
            acceptable_variants=task.acceptable_variants,
            numeric_tol=parse_tolerance(task.numeric_tolerance),
            context={
                "run_id":  output.run_id,
                "task_id": task_id,
                "model":   output.model_name,
                "phase":   "judge_comparison",
            },
            judge_model=judge_model,
        )

        row = db.query(JudgeComparison).filter_by(
            output_id=output_id, repeat_index=repeat_index
        ).first()
        setattr(row, f"judge_{slug}_score_percent", score)
        setattr(row, f"judge_{slug}_confidence", conf)
        setattr(row, f"judge_{slug}_token_input", tok_in)
        setattr(row, f"judge_{slug}_token_output", tok_out)
        setattr(row, f"judge_{slug}_notes", notes)
        setattr(row, f"judge_{slug}_evaluated_at", datetime.now(timezone.utc))
        db.commit()

        result["status"] = "done"
        result["score"]  = score

    except Exception as e:
        logger.error(f"[ERROR] task={task_id} output={output_id} rep={repeat_index} "
                     f"judge={judge_model}: {e}", exc_info=True)
        result["status"] = "error"
        result["error"]  = str(e)
    finally:
        db.close()

    return result


def log_summary(copied: int, cells: list) -> None:
    done    = [c for c in cells if c["status"] == "done"]
    skipped = [c for c in cells if c["status"] == "skipped"]
    dry_run = [c for c in cells if c["status"] == "dry-run"]
    errors  = [c for c in cells if c["status"] == "error"]

    logger.info("")
    logger.info("=" * 64)
    logger.info("JUDGE COMPARISON SUMMARY")
    logger.info("=" * 64)
    logger.info(f"  gpt-5-mini scores copied : {copied}")
    logger.info(f"  Alt-judge cells total    : {len(cells)}")
    logger.info(f"    done    : {len(done)}")
    logger.info(f"    skipped : {len(skipped)} (already filled)")
    logger.info(f"    dry-run : {len(dry_run)}")
    logger.info(f"    errors  : {len(errors)}")

    by_judge: dict = {}
    for c in done:
        by_judge.setdefault(c["judge_model"], []).append(c["score"])
    for jm, scores in sorted(by_judge.items()):
        mean = sum(scores) / len(scores)
        logger.info(f"  {jm:<24} mean score {mean:6.2f} (n={len(scores)})")

    if errors:
        logger.info("")
        logger.info("  Errors (first 20):")
        for c in errors[:20]:
            logger.info(f"    output={c['output_id']} rep={c['repeat_index']} "
                        f"judge={c['judge_model']}: {c['error']}")

    logger.info("=" * 64)


def main():
    parser = argparse.ArgumentParser(
        description="Score existing benchmark_outputs with alternative judge models "
                    "and persist all judges' results (incl. a copy of the production "
                    "score) into the judge_comparisons table."
    )
    parser.add_argument("--question-ids", default=None, dest="question_ids",
        help="Filter tasks by question_id (exact / prefix / range).")
    parser.add_argument("--task-ids", default=None, dest="task_ids",
        help="Filter tasks by BenchmarkTask.id (exact / range).")
    parser.add_argument("--judges", required=True,
        help="REQUIRED. Comma-separated alternative judge model name(s) to run.")
    parser.add_argument("--models", default=None,
        help="Comma-separated target model name(s) to judge. Default: all.")
    parser.add_argument("--repeats", type=int, default=1,
        help="judge_comparisons rows (repeat_index 1..N) per output (default 1).")
    parser.add_argument("--include-private", action="store_true", dest="include_private",
        help="Include is_public = 0 tasks (default: public only).")
    parser.add_argument("--skip-production-copy", action="store_true", dest="skip_production_copy",
        help="Skip copying the gpt-5-mini score onto row 1.")
    parser.add_argument("--overwrite", action="store_true",
        help="Re-fill judge columns even if already non-null (default: skip filled cells).")
    parser.add_argument("--max-workers", type=int, default=10, dest="max_workers",
        help="Max parallel judge calls (default 10).")
    parser.add_argument("--sequential", action="store_true",
        help="Run one judge call at a time.")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run",
        help="List the work without calling the judge or writing to the DB.")
    args = parser.parse_args()
    setup_error_log("judge_comparison")

    judges = [j.strip() for j in args.judges.split(",") if j.strip()]
    if not judges:
        logger.error("--judges is empty.")
        sys.exit(1)
    if pipeline.JUDGE_MODEL in judges:
        logger.error(f"--judges must not include {pipeline.JUDGE_MODEL!r} — the production "
                     f"judge is copied from benchmark_outputs automatically, never re-run.")
        sys.exit(1)
    unknown = [j for j in judges if j not in JUDGE_COLUMN_SLUGS]
    if unknown:
        logger.error(f"Unknown judge(s) {unknown} — not in JUDGE_COLUMN_SLUGS "
                     f"(backend/models.py). Known judges: {sorted(JUDGE_COLUMN_SLUGS)}. "
                     f"Add a migration + slug-map entry before using a new judge here.")
        sys.exit(1)
    if args.repeats < 1:
        logger.error("--repeats must be >= 1.")
        sys.exit(1)

    filter_qids     = _parse_question_ids(args.question_ids)
    filter_task_ids = _parse_task_ids(args.task_ids)
    filter_models   = [m.strip() for m in args.models.split(",")] if args.models else None

    if not filter_qids and not filter_task_ids:
        logger.error("No tasks specified. Use --question-ids or --task-ids.")
        sys.exit(1)

    # ── Build the work list ──────────────────────────────────────────────────
    db = SessionLocal()
    try:
        query = db.query(BenchmarkTask)
        if filter_qids:
            query = query.filter(_build_qid_filter(filter_qids))
        if filter_task_ids:
            query = query.filter(_build_task_id_filter(filter_task_ids))
        if not args.include_private:
            query = query.filter(BenchmarkTask.is_public == True)  # noqa: E712
        tasks = query.all()
        logger.info(f"Found {len(tasks)} task(s) matching filters "
                    f"({'incl. private' if args.include_private else 'public only'}).")

        outputs = []  # (task_id, output)
        for task in tasks:
            oq = db.query(BenchmarkOutput).filter_by(
                task_id=task.id, evaluation_method="judge"
            )
            if filter_models:
                oq = oq.filter(BenchmarkOutput.model_name.in_(filter_models))
            for output in oq.all():
                outputs.append((task.id, output))

        logger.info(f"Judge-scored outputs matching filters: {len(outputs)}")
        if not outputs:
            logger.info("Nothing to do.")
            return

        # ── Get-or-create rows + production copy ─────────────────────────────
        copied = 0
        cells  = []  # (task_id, output_id, repeat_index, judge_model)
        for task_id, output in outputs:
            for rep in range(1, args.repeats + 1):
                if args.dry_run:
                    if rep == 1 and not args.skip_production_copy:
                        copied += 1
                    for jm in judges:
                        cells.append((task_id, output.id, rep, jm, "would-run"))
                    continue

                row = _get_or_create_row(db, output, rep)
                if not args.skip_production_copy:
                    if copy_production_score(row, output, args.overwrite):
                        copied += 1
                for jm in judges:
                    slug = JUDGE_COLUMN_SLUGS[jm]
                    already_filled = getattr(row, f"judge_{slug}_score_percent") is not None
                    if already_filled and not args.overwrite:
                        cells.append((task_id, output.id, rep, jm, "skip"))
                    else:
                        cells.append((task_id, output.id, rep, jm, "run"))
        db.commit()
    finally:
        db.close()

    if args.dry_run:
        logger.info(f"gpt-5-mini scores that would be copied: {copied}")
        logger.info(f"Alt-judge cells that would run: {len(cells)}")
        for tid, oid, rep, jm, _ in cells[:20]:
            logger.info(f"  [DRY-RUN] task={tid} output={oid} rep={rep} judge={jm}")
        if len(cells) > 20:
            logger.info(f"  ... and {len(cells) - 20} more")
        return

    logger.info(f"gpt-5-mini scores copied: {copied}")
    to_run = [(tid, oid, rep, jm) for tid, oid, rep, jm, status in cells if status == "run"]
    skipped_n = len(cells) - len(to_run)
    logger.info(f"Alt-judge cells to run: {len(to_run)} (skipped {skipped_n} already-filled)")
    if not to_run:
        logger.info("Nothing left to judge.")
        return

    results = [{"task_id": tid, "output_id": oid, "repeat_index": rep,
                "judge_model": jm, "status": "skipped", "score": None, "error": None}
               for tid, oid, rep, jm, status in cells if status == "skip"]

    if args.sequential or len(to_run) == 1:
        for i, (tid, oid, rep, jm) in enumerate(to_run, 1):
            logger.info(f"[{i}/{len(to_run)}] output={oid} rep={rep} judge={jm}")
            results.append(judge_cell(tid, oid, rep, jm, args.dry_run))
    else:
        max_workers = min(args.max_workers, len(to_run))
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futs = {
                ex.submit(judge_cell, tid, oid, rep, jm, args.dry_run): (oid, rep, jm)
                for tid, oid, rep, jm in to_run
            }
            for n, fut in enumerate(as_completed(futs), 1):
                results.append(fut.result())
                if n % 25 == 0 or n == len(to_run):
                    logger.info(f"  ... {n}/{len(to_run)} judge calls done")

    log_summary(copied, results)


if __name__ == "__main__":
    main()
