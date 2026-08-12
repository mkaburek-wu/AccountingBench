"""
AccountingBench — Attach missing exercise documents to existing tasks
=====================================================================
The 12008933 payroll tasks were imported carrying only the reference table of
payroll values (Wichtige_Werte_ab_7.1.2026-1.pdf). The actual exercise text
lives in a separate Beispiel_NN_Angabe.pdf that was never linked, so the models
were asked to compute payroll figures for scenarios they could not see. Those
tasks average 3.2% against a corpus average of 63.8%, and ten of them score 0.0
across every model.

This script APPENDS the exercise PDF to a task's existing attached_files rather
than replacing it, so both documents reach the model.

Two details that matter and are easy to get wrong:

  * Paths must be ABSOLUTE. _split_attached_files() in pipeline.py hands each
    part to the URL resolver, and a bare filename raises
    "MissingSchema: No scheme supplied", which becomes a TaskLevelError that
    aborts the entire run — not just that task. That is exactly the defect the
    11830492 tasks are still suffering from.

  * The separator is " | ". _split_attached_files() splits on [\\n\\r;,|]+, so a
    comma would work too, but "|" is what the rest of the table already uses.

Re-running is safe: a task whose attached_files already names the file is
skipped, so entries are never duplicated.

Usage (run from the project root):
    python -m backend.add_task_attachments --dry-run
    python -m backend.add_task_attachments --yes
"""

import argparse
import os

from dotenv import load_dotenv

_root = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(os.path.dirname(_root), ".env"))

from backend.database import SessionLocal
from backend.models import BenchmarkTask

# Folder holding the exercise PDFs. Note it is 12008932 — one digit off the
# 12008933 question-id prefix. That is simply what the upload folder is called.
UPLOAD_SUBDIR = "12008932"

# question_id -> file to ADD (kept literal so the change stays auditable).
# 0027 and 0028 share Beispiel_03 on purpose: two questions on one exercise.
ATTACHMENT_MAP = {
    "12008933_0018": "Beispiel_10_Angabe.pdf",
    "12008933_0019": "Beispiel_09_Angabe.pdf",
    "12008933_0022": "Beispiel_07_Angabe.pdf",
    "12008933_0027": "Beispiel_03_Angabe.pdf",
    "12008933_0028": "Beispiel_03_Angabe.pdf",
    "12008933_0032": "Beispiel_01_Angabe.pdf",
}

SEPARATOR = " | "


def uploads_root() -> str:
    return os.path.join(_root, "uploads", UPLOAD_SUBDIR)


def absolute_path_for(filename: str) -> str:
    return os.path.abspath(os.path.join(uploads_root(), filename))


def main():
    ap = argparse.ArgumentParser(
        description="Append exercise PDFs to existing tasks' attached_files."
    )
    ap.add_argument("--dry-run", action="store_true", help="Show changes, write nothing")
    ap.add_argument("--yes", action="store_true", help="Skip the interactive confirmation")
    args = ap.parse_args()

    # ── Resolve every file up front; refuse to touch the DB if any is absent ──
    missing = [
        (qid, fn) for qid, fn in ATTACHMENT_MAP.items()
        if not os.path.isfile(absolute_path_for(fn))
    ]
    if missing:
        print(f"ABORT — {len(missing)} referenced file(s) not found under {uploads_root()}:")
        for qid, fn in missing:
            print(f"    {qid}  ->  {fn}")
        return

    print(f"All {len(set(ATTACHMENT_MAP.values()))} referenced PDF(s) found under "
          f"{uploads_root()}\n")

    db = SessionLocal()
    try:
        tasks = (
            db.query(BenchmarkTask)
            .filter(BenchmarkTask.question_id.in_(list(ATTACHMENT_MAP)))
            .all()
        )
        by_qid = {t.question_id: t for t in tasks}

        absent = [q for q in ATTACHMENT_MAP if q not in by_qid]
        if absent:
            print(f"ABORT — {len(absent)} question_id(s) not in the database: {absent}")
            return

        planned, skipped = [], []
        for qid, filename in ATTACHMENT_MAP.items():
            task = by_qid[qid]
            current = (task.attached_files or "").strip()
            new_path = absolute_path_for(filename)

            if filename in current:
                skipped.append((qid, filename))
                continue

            updated = f"{current}{SEPARATOR}{new_path}" if current else new_path
            planned.append((task, current, updated, filename))

        for task, current, updated, filename in planned:
            print(f"=== {task.question_id}  (task {task.id}) ===")
            print(f"  adding : {filename}")
            print(f"  before : {current or '(none)'}")
            print(f"  after  : {updated}")
            print()

        for qid, filename in skipped:
            print(f"  SKIP  {qid} — already references {filename}")

        print(f"\n{len(planned)} task(s) to update, {len(skipped)} already correct.")
        if not planned:
            return
        if args.dry_run:
            print("\n--dry-run: no changes made.")
            return
        if not args.yes:
            if input("\nType 'yes' to apply: ").strip().lower() != "yes":
                print("Aborted — nothing changed.")
                return

        for task, _current, updated, _filename in planned:
            task.attached_files = updated
        db.commit()

        print(f"\nUpdated {len(planned)} task(s).")
        print("\nNOTE: benchmark_outputs for these tasks were left untouched. Those answers")
        print("were produced WITHOUT the exercise document, so they should be deleted and")
        print("re-run rather than kept — re-scoring them would not change what the models")
        print("were actually shown.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
