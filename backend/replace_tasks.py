"""
AccountingBench — Replace task content in place, keeping the task id
====================================================================
Twelve Personalverrechnung tasks were rewritten after mistakes were found in
them. The corrected versions live in a normal ground-truth template, but they
carry NEW question_ids (12008932_*) while the rows already in the database use
the old 12008933_* series.

A plain `batch_run` import would insert twelve additional tasks and leave the
broken ones in place, because upsert_task() matches on question_id. This script
instead rewrites the EXISTING rows so that benchmark_tasks.id is preserved —
which keeps every foreign key, and keeps the ids stable for anyone referring to
them.

How it reuses the normal import path rather than duplicating it:

  1. set task.question_id to the new value on the row found by id, and commit;
  2. call upsert_task() with the sheet row — it now matches that same row by
     question_id and updates every field via setattr.

Doing it in that order is idempotent: if the run dies between the two steps,
re-running finds the task already renamed and simply re-applies the fields.

uploads_dir is passed on purpose. resolve_attached_files() turns the sheet's
relative paths into ABSOLUTE ones by searching under backend/uploads. A path
the attachment resolver cannot read is treated as a URL and raises
"MissingSchema: No scheme supplied", which becomes a TaskLevelError that aborts
the entire run — the defect the 11830492 tasks still suffer from.

Existing benchmark_outputs/benchmark_runs for these tasks answer the OLD
question and are deleted (after a JSON backup) so the tasks can be re-run.

Usage (run from the project root):
    python -m backend.replace_tasks --dry-run
    python -m backend.replace_tasks --yes
"""

import argparse
import json
import os
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv

_root = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(os.path.dirname(_root), ".env"))

from backend.database import SessionLocal
from backend.models import BenchmarkTask, BenchmarkOutput, BenchmarkRun
from backend.batch_run import upsert_task

EXCEL = os.path.join(_root, "uploads", "110826_Personalverrechnung_ground_truth_template.xlsx")
SHEET = "Questions"
UPLOADS_DIR = os.path.join(_root, "uploads")

# existing benchmark_tasks.id  ->  question_id of its replacement in the sheet
REPLACEMENTS = {
    6:  "12008932_0026",
    14: "12008932_0022",
    19: "12008932_0018",
    20: "12008932_0013",
    23: "12008932_0006",
    24: "12008932_0012",
    25: "12008932_0007",
    26: "12008932_0008",
    27: "12008932_0004",
    28: "12008932_0015",
    29: "12008932_0027",
    31: "12008932_0001",
}

# Single-cell corrections applied to the sheet before import, kept explicit so
# they stay visible instead of being buried in a hand-edited spreadsheet.
# 12008932_0006 carries descriptive text ("Beispiel 1; GF; 15 % Beteiligung; …")
# where a framework belongs; left alone the task drops out of every
# regulatory-framework bucket in results.js.
CELL_OVERRIDES = {
    ("12008932_0006", "regulatory_framework"): "austrian_tax_law",
}


def load_rows():
    df = pd.read_excel(EXCEL, sheet_name=SHEET)
    df["question_id"] = df["question_id"].astype(str).str.strip()
    for (qid, col), value in CELL_OVERRIDES.items():
        mask = df["question_id"] == qid
        if mask.any():
            old = df.loc[mask, col].iloc[0]
            df.loc[mask, col] = value
            print(f"  OVERRIDE {qid}.{col}: {str(old)[:60]!r} -> {value!r}")
    return {r["question_id"]: r for _, r in df.iterrows()}


def main():
    ap = argparse.ArgumentParser(description="Replace task content in place, keeping task ids.")
    ap.add_argument("--dry-run", action="store_true", help="Show what would change, write nothing")
    ap.add_argument("--yes", action="store_true", help="Skip the interactive confirmation")
    ap.add_argument("--backup-dir", default=os.environ.get("TEMP", "."),
                    help="Where to write the deleted-rows JSON backup")
    args = ap.parse_args()

    if not os.path.isfile(EXCEL):
        print(f"ABORT — Excel not found: {EXCEL}")
        return

    print(f"Excel : {EXCEL}")
    print(f"Sheet : {SHEET}\n")
    rows = load_rows()

    absent = [q for q in REPLACEMENTS.values() if q not in rows]
    if absent:
        print(f"ABORT — {len(absent)} question_id(s) not in the sheet: {absent}")
        return

    db = SessionLocal()
    try:
        tasks = {t.id: t for t in db.query(BenchmarkTask)
                 .filter(BenchmarkTask.id.in_(list(REPLACEMENTS))).all()}
        missing_ids = [i for i in REPLACEMENTS if i not in tasks]
        if missing_ids:
            print(f"ABORT — task id(s) not in the database: {missing_ids}")
            return

        # A new question_id must not already belong to a DIFFERENT task.
        for tid, qid in REPLACEMENTS.items():
            clash = db.query(BenchmarkTask).filter(
                BenchmarkTask.question_id == qid, BenchmarkTask.id != tid
            ).first()
            if clash:
                print(f"ABORT — {qid} already belongs to task {clash.id}, cannot reassign to {tid}")
                return

        n_out = db.query(BenchmarkOutput).filter(
            BenchmarkOutput.task_id.in_(list(REPLACEMENTS))).count()
        n_run = db.query(BenchmarkRun).filter(
            BenchmarkRun.task_id.in_(list(REPLACEMENTS))).count()

        print("\n=== Replacements ===")
        for tid in sorted(REPLACEMENTS):
            t, qid = tasks[tid], REPLACEMENTS[tid]
            row = rows[qid]
            print(f"  task {tid:4}  {t.question_id:16} -> {qid:16}  "
                  f"{str(row['answer_type']):11} prompt={len(str(row['prompt'])):5} chars")

        print(f"\n=== Results to delete ===")
        print(f"  benchmark_outputs: {n_out}")
        print(f"  benchmark_runs   : {n_run}")

        if args.dry_run:
            print("\n--dry-run: no changes made.")
            return
        if not args.yes:
            if input("\nType 'yes' to apply: ").strip().lower() != "yes":
                print("Aborted — nothing changed.")
                return

        # ── Back up everything that is about to be deleted ────────────────────
        def dump(objs):
            out = []
            for o in objs:
                out.append({c.name: str(getattr(o, c.name))
                            for c in o.__table__.columns})
            return out

        backup = {
            "created": datetime.now().isoformat(),
            "task_ids": sorted(REPLACEMENTS),
            "tasks_before": dump(db.query(BenchmarkTask).filter(
                BenchmarkTask.id.in_(list(REPLACEMENTS))).all()),
            "outputs": dump(db.query(BenchmarkOutput).filter(
                BenchmarkOutput.task_id.in_(list(REPLACEMENTS))).all()),
            "runs": dump(db.query(BenchmarkRun).filter(
                BenchmarkRun.task_id.in_(list(REPLACEMENTS))).all()),
        }
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = os.path.join(args.backup_dir, f"replace_tasks_backup_{stamp}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(backup, fh, ensure_ascii=False, indent=2)
        print(f"\nBackup written: {path}")

        # ── 1. rename, so upsert_task can match the existing row ─────────────
        for tid, qid in REPLACEMENTS.items():
            tasks[tid].question_id = qid
        db.commit()
        print(f"Renamed {len(REPLACEMENTS)} question_id(s).")

        # ── 2. apply the sheet through the normal import path ────────────────
        for tid in sorted(REPLACEMENTS):
            qid = REPLACEMENTS[tid]
            task = upsert_task(db, rows[qid], approved=True,
                               user_id="batch_admin", uploads_dir=UPLOADS_DIR)
            if task.id != tid:
                print(f"  *** WARNING: {qid} landed on task {task.id}, expected {tid}")

        # ── 3. drop the now-stale results ────────────────────────────────────
        d_out = db.query(BenchmarkOutput).filter(
            BenchmarkOutput.task_id.in_(list(REPLACEMENTS))).delete(synchronize_session=False)
        d_run = db.query(BenchmarkRun).filter(
            BenchmarkRun.task_id.in_(list(REPLACEMENTS))).delete(synchronize_session=False)
        db.commit()

        print(f"\nReplaced {len(REPLACEMENTS)} task(s).")
        print(f"Deleted {d_out} output row(s) and {d_run} run row(s).")
        print("\nRe-run them with:")
        print("  python -m backend.rerun_model --task-ids "
              + ",".join(str(i) for i in sorted(REPLACEMENTS)))

    finally:
        db.close()


if __name__ == "__main__":
    main()
