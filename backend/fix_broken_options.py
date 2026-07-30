"""
AccountingBench — Fix broken options data
============================================
Some choice tasks were imported with an older, less capable version of
parse_options() (backend/batch_run.py) that failed to detect their format
and fell back to options={"raw": "<unparsed blob>"}. Since pipeline.py
derives valid_choices from the options dict keys, a "raw" fallback means
valid_choices=["RAW"] — every model's real letter answer (A, B, C...) gets
filtered out as invalid, producing an empty final_answer regardless of
which model answered or how well.

The CURRENT parse_options() already handles these formats correctly (verified
by testing it directly against the stored raw text). This script re-parses
every single_choice/multi_choice task stuck with options={"raw": ...} using
the current parser and updates benchmark_tasks.options in place if it now
yields a proper dict. Pure data fix — no API calls, no score changes here
(re-scoring the affected models is a separate step since their historical
empty answers can't be recovered and need a real rerun).

Usage (run from the project root):
    python -m backend.fix_broken_options --dry-run
    python -m backend.fix_broken_options --yes
"""

import argparse
import json
import os

from dotenv import load_dotenv

_root = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(os.path.dirname(_root), ".env"))

from backend.database import SessionLocal
from backend.models import BenchmarkTask
from backend.batch_run import parse_options


def find_broken_tasks(db):
    tasks = (
        db.query(BenchmarkTask)
        .filter(BenchmarkTask.answer_type.in_(["single_choice", "multi_choice"]))
        .filter(BenchmarkTask.options.isnot(None))
        .all()
    )
    broken = []
    for t in tasks:
        if isinstance(t.options, dict) and list(t.options.keys()) == ["raw"]:
            broken.append(t)
    return broken


def main():
    parser = argparse.ArgumentParser(description="Fix tasks with options={'raw': ...} by re-parsing.")
    parser.add_argument("--dry-run", action="store_true", help="Print what would change, no writes")
    parser.add_argument("--yes", action="store_true", help="Skip the interactive confirmation prompt")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        broken = find_broken_tasks(db)
        if not broken:
            print("No tasks with options={'raw': ...} found — nothing to do.")
            return

        print(f"Found {len(broken)} task(s) with unparsed options:\n")
        fixable, still_broken = [], []
        for t in broken:
            reparsed = parse_options(t.options["raw"])
            if isinstance(reparsed, dict) and list(reparsed.keys()) != ["raw"]:
                fixable.append((t, reparsed))
                print(f"  FIX   {t.question_id}  {t.options['raw'][:60]!r}...")
                print(f"        -> {reparsed}")
            else:
                still_broken.append(t)
                print(f"  SKIP  {t.question_id}  still unparseable, left as-is")

        print(f"\n{len(fixable)} task(s) will be fixed, {len(still_broken)} remain unparseable "
              f"(need manual review).")

        if args.dry_run:
            print("\n--dry-run: no changes made.")
            return

        if not args.yes:
            confirm = input("\nType 'yes' to apply these fixes: ").strip().lower()
            if confirm != "yes":
                print("Aborted — nothing changed.")
                return

        for t, reparsed in fixable:
            t.options = reparsed
        db.commit()

        print(f"\nUpdated {len(fixable)} task(s).")

    finally:
        db.close()


if __name__ == "__main__":
    main()
