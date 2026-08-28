"""
AccountingBench — Judge-Comparison Experiment (CSV, read-only)
============================================================
Re-scores existing benchmark_outputs rows with one or more ALTERNATIVE judge
models and writes every result to a CSV. Nothing in the database is touched:
this is an offline experiment to see how the leaderboard would move under a
different LLM-as-a-judge.

The production judge stays fixed — `pipeline.JUDGE_MODEL` ("gpt-5-mini") — and
must never change (score comparability). This script only *reads* stored
final answers and calls `pipeline.call_judge(..., judge_model=<alt>)`.

Usage
-----
# Compare two alt judges against the stored gpt-5-mini scores, public tasks only
python -m backend.judge_experiment \
    --question-ids "11830492" \
    --judges "gpt-5.4,gpt-5-mini"

# Restrict to specific target model(s), run each judge 3x to measure judge variance
python -m backend.judge_experiment \
    --task-ids "19,42,100:110" \
    --models "gpt-5.4,Kimi-K2.6" \
    --judges "gpt-5.4,claude-sonnet-4.5" \
    --repeats 3

# Quick smoke test
python -m backend.judge_experiment --task-ids "19" --judges "gpt-5-mini" --limit 5 --sequential

Flags
-----
--question-ids   Filter tasks by question_id (exact / prefix / range) — same
                 syntax as rerun_model.py / rejudge.py.
--task-ids       Filter tasks by BenchmarkTask.id (exact / range).
--judges         REQUIRED. Comma-separated judge model name(s) to test. Each
                 must be an OpenAI-compatible entry in MODEL_REGISTRY_JSON
                 (native anthropic_foundry deployments are rejected by
                 call_judge). Include "gpt-5-mini" to get a same-judge
                 re-run baseline in the same CSV.
--models         Optional. Comma-separated target model name(s) whose outputs
                 are re-judged. Default: every model with a judge-scored
                 output on the selected tasks.
--repeats        Times to call each judge per output (default 1). >1 lets you
                 measure judge self-consistency at temperature 0.
--include-private  Include is_public = 0 tasks (default: public only, matching
                 what the site reports).
--limit          Cap the number of (task, target-model) pairs before the judge
                 cross-product. Handy for smoke tests.
--max-workers    Max parallel judge calls (default 10).
--sequential     Run one judge call at a time.
--out            CSV output path. Default:
                 backend/output/judge_experiment_<timestamp>.csv
--dry-run        List the work (tasks x models x judges x repeats) and write the
                 CSV with metadata + stored prod scores filled in but no judge
                 calls (score_percent blank, error="dry-run").

Output CSV columns
------------------
question_id, task_id, model_name, category, task_type, answer_type,
regulatory_framework, education_level, is_public, prod_judge_model,
prod_judge_score, prod_final_score, judge_model, repeat, score_percent,
confidence, notes, judge_tok_in, judge_tok_out, gold_answer, final_answer, error
"""

import argparse
import csv
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
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
logger = logging.getLogger("judge_experiment")

# ── Imports (after env is loaded) ─────────────────────────────────────────────
from backend.database import SessionLocal
from backend.models   import BenchmarkTask, BenchmarkOutput
from backend.batch_utils import setup_error_log
from backend.processing import pipeline
from backend.processing.pipeline import call_judge, parse_tolerance
from backend.rerun_model import (
    _parse_question_ids, _build_qid_filter,
    _parse_task_ids, _build_task_id_filter,
)

CSV_FIELDS = [
    "question_id", "task_id", "model_name",
    "category", "task_type", "answer_type",
    "regulatory_framework", "education_level", "is_public",
    "prod_judge_model", "prod_judge_score", "prod_final_score",
    "judge_model", "repeat",
    "score_percent", "confidence", "notes",
    "judge_tok_in", "judge_tok_out",
    "gold_answer", "final_answer", "error",
]


def judge_one(task_id: int, model_name: str, judge_model: str, repeat: int,
              dry_run: bool) -> dict:
    """Re-score one existing BenchmarkOutput with `judge_model`. Read-only —
    returns a CSV row dict, never writes to the DB."""
    row = {k: None for k in CSV_FIELDS}
    row.update(task_id=task_id, model_name=model_name,
               judge_model=judge_model, repeat=repeat,
               prod_judge_model=pipeline.JUDGE_MODEL)

    db = SessionLocal()
    try:
        task = db.query(BenchmarkTask).filter_by(id=task_id).first()
        output = db.query(BenchmarkOutput).filter_by(
            task_id=task_id, model_name=model_name
        ).first()
        if task is None or output is None:
            row["error"] = "task or output not found"
            return row

        row.update(
            question_id          = task.question_id,
            category             = task.category,
            task_type            = task.task_type,
            answer_type          = task.answer_type,
            regulatory_framework = task.regulatory_framework,
            education_level       = task.education_level,
            is_public            = int(bool(task.is_public)),
            prod_judge_score     = output.judge_score_percent,
            prod_final_score     = output.final_score_percent,
            gold_answer          = task.gold_answer,
            final_answer         = output.final_answer,
        )

        if not (output.final_answer or "").strip():
            row["error"] = "empty final_answer — nothing to judge"
            return row

        if dry_run:
            row["error"] = "dry-run"
            return row

        score, conf, notes, tok_in, tok_out = call_judge(
            task.prompt, output.final_answer, task.gold_answer,
            grading_criteria=task.grading_criteria,
            acceptable_variants=task.acceptable_variants,
            numeric_tol=parse_tolerance(task.numeric_tolerance),
            context={
                "run_id":  output.run_id,
                "task_id": task_id,
                "model":   model_name,
                "phase":   "judge_experiment",
            },
            judge_model=judge_model,
        )
        row.update(score_percent=score, confidence=conf, notes=notes,
                   judge_tok_in=tok_in, judge_tok_out=tok_out)

    except Exception as e:
        logger.error(f"[ERROR] task={task_id} model={model_name} judge={judge_model}: {e}",
                     exc_info=True)
        row["error"] = str(e)
    finally:
        db.close()

    return row


def _clip(v, n=400):
    s = "" if v is None else str(v)
    return s if len(s) <= n else s[:n] + f"…(+{len(s) - n})"


def log_summary(rows: list) -> None:
    scored = [r for r in rows if r["score_percent"] is not None]
    errors = [r for r in rows if r["error"] and r["error"] != "dry-run"]

    logger.info("")
    logger.info("=" * 64)
    logger.info("JUDGE EXPERIMENT SUMMARY")
    logger.info("=" * 64)
    logger.info(f"  Rows written : {len(rows)}")
    logger.info(f"  Scored       : {len(scored)}")
    logger.info(f"  Errors       : {len(errors)}")

    # Per-judge: mean score, and mean delta vs the stored production judge score.
    by_judge: dict = {}
    for r in scored:
        by_judge.setdefault(r["judge_model"], []).append(r)

    for jm, rs in sorted(by_judge.items()):
        mean_new = sum(x["score_percent"] for x in rs) / len(rs)
        deltas   = [x["score_percent"] - x["prod_judge_score"]
                    for x in rs if x["prod_judge_score"] is not None]
        d_txt = ""
        if deltas:
            mean_d = sum(deltas) / len(deltas)
            mad    = sum(abs(d) for d in deltas) / len(deltas)
            d_txt  = f" | vs {pipeline.JUDGE_MODEL}: mean Δ {mean_d:+.2f}, mean |Δ| {mad:.2f} (n={len(deltas)})"
        logger.info(f"  {jm:<28} mean score {mean_new:6.2f} (n={len(rs)}){d_txt}")

    if errors:
        logger.info("")
        logger.info("  Errors (first 20):")
        for r in errors[:20]:
            logger.info(f"    task={r['task_id']} model={r['model_name']} "
                        f"judge={r['judge_model']}: {_clip(r['error'], 160)}")

    logger.info("=" * 64)


def main():
    parser = argparse.ArgumentParser(
        description="Re-score existing benchmark_outputs with alternative judge "
                    "models and write results to CSV. Read-only — no DB writes."
    )
    parser.add_argument("--question-ids", default=None, dest="question_ids",
        help="Filter tasks by question_id (exact / prefix / range).")
    parser.add_argument("--task-ids", default=None, dest="task_ids",
        help="Filter tasks by BenchmarkTask.id (exact / range).")
    parser.add_argument("--judges", required=True,
        help="REQUIRED. Comma-separated judge model name(s) to test.")
    parser.add_argument("--models", default=None,
        help="Comma-separated target model name(s) to re-judge. Default: all.")
    parser.add_argument("--repeats", type=int, default=1,
        help="Judge calls per output per judge (default 1).")
    parser.add_argument("--include-private", action="store_true", dest="include_private",
        help="Include is_public = 0 tasks (default: public only).")
    parser.add_argument("--limit", type=int, default=None,
        help="Cap (task, target-model) pairs before the judge cross-product.")
    parser.add_argument("--max-workers", type=int, default=10, dest="max_workers",
        help="Max parallel judge calls (default 10).")
    parser.add_argument("--sequential", action="store_true",
        help="Run one judge call at a time.")
    parser.add_argument("--out", default=None,
        help="CSV output path. Default: backend/output/judge_experiment_<ts>.csv")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run",
        help="List the work and write the CSV with metadata + prod scores only "
             "(no judge calls).")
    args = parser.parse_args()
    setup_error_log("judge_experiment")

    judges = [j.strip() for j in args.judges.split(",") if j.strip()]
    if not judges:
        logger.error("--judges is empty.")
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

    out_path = Path(args.out) if args.out else (
        _ROOT / "backend" / "output" /
        f"judge_experiment_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)

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

        pairs = []  # (task_id, question_id, model_name)
        for task in tasks:
            oq = db.query(BenchmarkOutput).filter_by(
                task_id=task.id, evaluation_method="judge"
            )
            if filter_models:
                oq = oq.filter(BenchmarkOutput.model_name.in_(filter_models))
            for output in oq.all():
                pairs.append((task.id, task.question_id, output.model_name))
    finally:
        db.close()

    pairs.sort()
    if args.limit is not None:
        pairs = pairs[:args.limit]

    work = [
        (tid, qid, model, jm, rep)
        for (tid, qid, model) in pairs
        for jm in judges
        for rep in range(1, args.repeats + 1)
    ]

    logger.info(f"Target (task, model) pairs : {len(pairs)}")
    logger.info(f"Judges                     : {judges}")
    logger.info(f"Repeats                    : {args.repeats}")
    logger.info(f"Total judge calls          : {len(work)}")
    logger.info(f"CSV out                    : {out_path}")
    if not work:
        logger.info("Nothing to do.")
        return

    # ── Run ────────────────────────────────────────────────────────────────────
    rows = []
    if args.dry_run or args.sequential or len(work) == 1:
        for i, (tid, qid, model, jm, rep) in enumerate(work, 1):
            logger.info(f"[{i}/{len(work)}] {qid} / {model} / judge={jm} / rep={rep}")
            rows.append(judge_one(tid, model, jm, rep, args.dry_run))
    else:
        max_workers = min(args.max_workers, len(work))
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futs = {
                ex.submit(judge_one, tid, model, jm, rep, args.dry_run):
                    (qid, model, jm, rep)
                for (tid, qid, model, jm, rep) in work
            }
            for n, fut in enumerate(as_completed(futs), 1):
                rows.append(fut.result())
                if n % 25 == 0 or n == len(work):
                    logger.info(f"  ... {n}/{len(work)} judge calls done")

    # ── Write CSV ─────────────────────────────────────────────────────────────
    rows.sort(key=lambda r: (r.get("question_id") or "", r.get("model_name") or "",
                             r.get("judge_model") or "", r.get("repeat") or 0))
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    logger.info(f"Wrote {len(rows)} row(s) -> {out_path}")

    if not args.dry_run:
        log_summary(rows)


if __name__ == "__main__":
    main()
