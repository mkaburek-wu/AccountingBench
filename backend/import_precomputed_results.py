"""
AccountingBench — Pre-computed Results Importer
=================================================
Imports already-scored model outputs from an Excel file that was produced
by an EXTERNAL run (not this repo's run_pipeline()). Unlike batch_run.py /
rerun_model.py, this script never calls a model API or the judge — it
writes benchmark_tasks / benchmark_runs / benchmark_outputs rows directly
from the Excel data.

Two supported Excel layouts:

  1. Task + output sheets (default) — two sheets in the same workbook:
       "Questions" — same layout as batch_run.py's ground-truth template
                     (question_id, task_type, prompt, answer_type,
                     gold_answer, ...). Tasks are upserted by question_id.
       "Outputs"   — one row per (question_id, model), see column list below.

  2. Outputs-only (--outputs-only) — a single output sheet, no task sheet.
     Used when the tasks already exist in the DB (e.g. backfilling results
     for "old" models against the original dataset) — tasks are looked up
     by question_id instead of upserted; a task not found in the DB is an
     error for that row, not a fabricated task.

Output sheet columns (either layout): Model, question_id,
model_answer_1/2/3, model_confidence_1/2/3, final_answer,
avg_model_confidence, score_percent_sc_mc, judge_score_percent,
judge_confidence, final_score_percent, evaluation_method, token_input,
token_output, token_reasoning, evaluated_at_utc, evaluation_notes

Usage (run from the accountingbench/ root):
    python -m backend.import_precomputed_results --file backend/uploads/results_IFRS_n44.xlsx --dry-run
    python -m backend.import_precomputed_results --file backend/uploads/results_IFRS_n44.xlsx --limit 2
    python -m backend.import_precomputed_results --file backend/uploads/results_IFRS_n44.xlsx

    # Outputs-only — tasks already exist in the DB, just backfill model results
    python -m backend.import_precomputed_results --file backend/output_old_models.xlsx --outputs-sheet Output --outputs-only --dry-run
    python -m backend.import_precomputed_results --file backend/output_old_models.xlsx --outputs-sheet Output --outputs-only --skip-existing

Options:
    --file          Path to the Excel file (required)
    --questions-sheet  Sheet name for tasks (default: Questions). Ignored with --outputs-only.
    --outputs-sheet    Sheet name for model outputs (default: Outputs)
    --outputs-only     Skip the Questions sheet — look up existing tasks in the
                        DB by question_id instead of upserting them. A task
                        missing from the DB is reported as an error, not created.
    --dry-run       Parse and validate only, no DB writes
    --limit         Only process the first N tasks (useful for testing)
    --user          User ID to attribute submissions to (default: BATCH_USER_ID from .env)
    --rename-model  Rename a model on import, e.g. "DeepSeek-V3.2-2:DeepSeek-V3.2".
                    Repeatable. Applied to the Outputs sheet before grouping.
    --skip-existing Skip (task, model) pairs that already have a benchmark_output row
"""

import argparse
import logging
import os
import uuid
from datetime import datetime, timezone

import pandas as pd
from dotenv import load_dotenv

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_root, ".env"))

from backend.database import SessionLocal
from backend.models import BenchmarkTask, BenchmarkRun, BenchmarkOutput
from backend.batch_run import read_excel, upsert_task, safe, DEFAULT_UPLOADS_DIR
from backend.batch_utils import (
    ensure_batch_user,
    create_submission,
    get_existing_model_outputs,
    log_summary,
    setup_error_log,
    BATCH_USER_ID,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("import_precomputed_results")

SYSTEM_PROMPT_VERSION = "v3_types"
DATASET_VERSION = "v3"
JUDGE_MODEL = "gpt-5-mini"

# Model names that differ between this Excel's naming and the existing DB/
# .env MODEL_REGISTRY_JSON convention — normalized on import so results join
# with any pre-existing rows for the same model instead of forming a
# separate bucket. Always applied; --rename-model can add more.
DEFAULT_RENAMES = {
    "DeepSeek-V3.2-2": "DeepSeek-V3.2",
}

OUTPUT_COLUMNS = [
    "Model", "question_id",
    "model_answer_1", "model_confidence_1",
    "model_answer_2", "model_confidence_2",
    "model_answer_3", "model_confidence_3",
    "final_answer", "avg_model_confidence",
    "score_percent_sc_mc", "judge_score_percent", "judge_confidence",
    "final_score_percent", "evaluation_method",
    "token_input", "token_output", "token_reasoning",
    "evaluated_at_utc", "evaluation_notes",
]


def _num(val):
    """None/NaN-safe float coercion."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    return float(val)


def _int(val):
    n = _num(val)
    return int(n) if n is not None else None


def _dt(val):
    """Parse an evaluated_at_utc cell (ISO string or datetime) to a datetime, or None."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(str(val))
    except ValueError:
        return None


def read_outputs(file_path: str, sheet_name: str) -> pd.DataFrame:
    logger.info(f"Reading {file_path} — sheet '{sheet_name}'")
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    missing = [c for c in OUTPUT_COLUMNS if c not in df.columns]
    if missing:
        raise SystemExit(f"Outputs sheet is missing required columns: {missing}")
    logger.info(f"Found {len(df)} output row(s).")
    return df


def apply_renames(df: pd.DataFrame, renames: dict) -> pd.DataFrame:
    if not renames:
        return df
    df = df.copy()
    for old, new in renames.items():
        n = (df["Model"] == old).sum()
        if n:
            logger.info(f"  Renaming model '{old}' → '{new}' ({n} row(s))")
            df.loc[df["Model"] == old, "Model"] = new
    return df


def write_outputs(
    db, task: BenchmarkTask, out_rows: pd.DataFrame, user_id: str, skip_existing: bool, source_filename: str
) -> dict:
    qid = task.question_id
    result = {"question_id": qid, "status": "unknown", "submission_id": None, "error": None, "models": None}

    try:
        if skip_existing:
            requested_models = out_rows["Model"].dropna().tolist()
            already_have = get_existing_model_outputs(db, task.id, requested_models)
            if already_have:
                out_rows = out_rows[~out_rows["Model"].isin(already_have)]
            if out_rows.empty:
                logger.info(f"[SKIP] {qid} — all requested models already have output rows.")
                result["status"] = "skipped"
                return result

        sub = create_submission(db, task, user_id)
        sub.status = "done"
        sub.completed_at = datetime.now(timezone.utc)
        db.commit()
        result["submission_id"] = sub.id

        run_id = f"run_import_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        models_written = []

        for _, o in out_rows.iterrows():
            model_name = safe(o.get("Model"))
            if not model_name:
                continue

            db.add(BenchmarkRun(
                run_id=run_id,
                task_id=task.id,
                model_name=model_name,
                run_timestamp=datetime.now(timezone.utc),
                temperature=0.0,
                n_trials=3,
                system_prompt_version=SYSTEM_PROMPT_VERSION,
                dataset_version=DATASET_VERSION,
                judge_model=JUDGE_MODEL,
                inference_notes=f"Imported from {source_filename} (external run)",
            ))

            db.add(BenchmarkOutput(
                run_id=run_id,
                task_id=task.id,
                model_name=model_name,
                model_answer_1=safe(o.get("model_answer_1")) or None,
                model_confidence_1=_num(o.get("model_confidence_1")),
                model_answer_2=safe(o.get("model_answer_2")) or None,
                model_confidence_2=_num(o.get("model_confidence_2")),
                model_answer_3=safe(o.get("model_answer_3")) or None,
                model_confidence_3=_num(o.get("model_confidence_3")),
                final_answer=safe(o.get("final_answer")) or None,
                avg_model_confidence=_num(o.get("avg_model_confidence")),
                score_percent_sc_mc=_num(o.get("score_percent_sc_mc")),
                judge_score_percent=_num(o.get("judge_score_percent")),
                judge_confidence=_num(o.get("judge_confidence")),
                final_score_percent=_num(o.get("final_score_percent")),
                evaluation_method=safe(o.get("evaluation_method")) or None,
                token_input=_int(o.get("token_input")),
                token_output=_int(o.get("token_output")),
                token_reasoning=_int(o.get("token_reasoning")),
                evaluated_at_utc=_dt(o.get("evaluated_at_utc")) or datetime.now(timezone.utc),
                evaluation_notes=safe(o.get("evaluation_notes")) or None,
            ))
            models_written.append(model_name)

        db.commit()
        result["status"] = "done"
        result["models"] = ", ".join(models_written)
        logger.info(f"[DONE] {qid} → submission {sub.id} — {len(models_written)} model output(s) written.")

    except Exception as e:
        db.rollback()
        logger.error(f"[ERROR] {qid}: {e}", exc_info=True)
        result["status"] = "error"
        result["error"] = str(e)

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Import already-scored tasks/outputs from an Excel file (no live model calls)."
    )
    parser.add_argument("--file", required=True, help="Path to the Excel file")
    parser.add_argument("--questions-sheet", default="Questions", help="Sheet name for tasks (default: Questions). Ignored with --outputs-only")
    parser.add_argument("--outputs-sheet", default="Outputs", help="Sheet name for model outputs (default: Outputs)")
    parser.add_argument(
        "--outputs-only", action="store_true",
        help="Skip the Questions sheet — look up existing tasks in the DB by question_id instead of upserting them",
    )
    parser.add_argument("--dry-run", action="store_true", help="Parse and validate only, no DB writes")
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N tasks")
    parser.add_argument("--user", default=None, help="User ID to attribute submissions to")
    parser.add_argument(
        "--rename-model", action="append", default=[],
        help='Rename a model on import, e.g. "DeepSeek-V3.2-2:DeepSeek-V3.2" (repeatable)',
    )
    parser.add_argument(
        "--skip-existing", action="store_true",
        help="Skip (task, model) pairs that already have a benchmark_output row",
    )
    args = parser.parse_args()

    setup_error_log("import_precomputed_results")

    renames = dict(DEFAULT_RENAMES)
    for spec in args.rename_model:
        if ":" not in spec:
            raise SystemExit(f"--rename-model must be OLD:NEW, got: {spec!r}")
        old, new = spec.split(":", 1)
        renames[old.strip()] = new.strip()

    out_df = read_outputs(args.file, args.outputs_sheet)
    out_df = apply_renames(out_df, renames)

    q_row_by_qid = {}
    if args.outputs_only:
        q_df = None
        qids = sorted(out_df["question_id"].dropna().unique().tolist())
        if args.limit:
            qids = qids[: args.limit]
            logger.info(f"--limit {args.limit}: processing first {len(qids)} task(s).")
    else:
        q_df = read_excel(args.file, args.questions_sheet)
        if args.limit:
            q_df = q_df.head(args.limit)
            logger.info(f"--limit {args.limit}: processing first {len(q_df)} task(s).")
        qids = [safe(r.get("question_id")) for _, r in q_df.iterrows()]
        q_row_by_qid = {safe(r.get("question_id")): r for _, r in q_df.iterrows()}

    out_by_qid = {qid: grp for qid, grp in out_df.groupby("question_id")}

    all_models = sorted(out_df["Model"].dropna().unique().tolist())
    logger.info(f"Models present in Outputs sheet: {all_models}")

    # ── Validation (always runs, even outside --dry-run) ──────────────────────
    problems = []
    if args.outputs_only:
        db = SessionLocal()
        try:
            existing = {
                r.question_id
                for r in db.query(BenchmarkTask.question_id).filter(BenchmarkTask.question_id.in_(qids)).all()
            }
        finally:
            db.close()
        missing_tasks = [qid for qid in qids if qid not in existing]
        for qid in missing_tasks:
            problems.append(f"{qid}: no matching task in the database (--outputs-only requires existing tasks)")

    for qid in qids:
        rows = out_by_qid.get(qid)
        if rows is None or rows.empty:
            problems.append(f"{qid}: no Outputs rows found")
            continue
        dupes = rows["Model"].value_counts()
        dupes = dupes[dupes > 1]
        if len(dupes):
            problems.append(f"{qid}: duplicate output rows for model(s) {list(dupes.index)}")
        missing_models = set(all_models) - set(rows["Model"].dropna().tolist())
        if missing_models:
            problems.append(f"{qid}: missing output rows for model(s) {sorted(missing_models)}")

    if problems:
        logger.warning(f"Found {len(problems)} validation issue(s):")
        for p in problems:
            logger.warning(f"  {p}")
    else:
        logger.info("Validation OK — every task has one output row per model, no duplicates.")

    if args.dry_run:
        logger.info("=== DRY RUN — no writes ===")
        for qid in qids:
            rows = out_by_qid.get(qid)
            n = len(rows) if rows is not None else 0
            action = "would backfill outputs for" if args.outputs_only else "would insert 1 task +"
            logger.info(f"  {qid}: {action} {n} run/output pairs")
        logger.info(f"=== {len(qids)} task(s), {sum(len(out_by_qid.get(q, [])) for q in qids)} output row(s) would be processed ===")
        return

    db = SessionLocal()
    try:
        ensure_batch_user(db)
        user_id = args.user or BATCH_USER_ID
    finally:
        db.close()

    source_filename = os.path.basename(args.file)
    results = []
    for qid in qids:
        rows = out_by_qid.get(qid)
        if rows is None or rows.empty:
            logger.warning(f"[SKIP] {qid} — no Outputs rows, task not imported.")
            results.append({"question_id": qid, "status": "skipped", "submission_id": None, "error": None})
            continue

        db = SessionLocal()
        try:
            if args.outputs_only:
                task = db.query(BenchmarkTask).filter_by(question_id=qid).first()
                if not task:
                    logger.error(f"[ERROR] {qid} — task not found in DB (outputs-only mode).")
                    results.append({
                        "question_id": qid, "status": "error", "submission_id": None,
                        "error": "task not found in DB",
                    })
                    continue
            else:
                task = upsert_task(
                    db, q_row_by_qid[qid], approved=True, user_id=user_id, uploads_dir=DEFAULT_UPLOADS_DIR
                )
            result = write_outputs(db, task, rows, user_id, args.skip_existing, source_filename)
        finally:
            db.close()
        results.append(result)

    log_summary(results, title="IMPORT SUMMARY")


if __name__ == "__main__":
    main()
