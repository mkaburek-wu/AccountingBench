"""
AccountingBench — Backfill stale SC/MC scores
================================================
A narrow batch of multi_choice tasks (question_id 12016904_0270-0287) was
scored during an ~8-minute window on 2026-06-15 under a scoring bug that
has since been fixed in score_sc_mc_percent() (backend/processing/pipeline.py).
Their stored score_percent_sc_mc / final_score_percent are stale zeros even
though the stored final_answer is correct — e.g. task 727 (12016904_0276)
shows final_answer="A,B,C" matching gold_answer="A,B,C" but score=0.0.

This script recomputes score_sc_mc_percent(final_answer, gold_answer) for
every sc_mc_formula output row using the CURRENT (correct) formula and
fixes any row whose stored score doesn't match — no API calls needed,
since the stored final_answer is already correct. Safe to run multiple
times — a clean DB reports zero mismatches and does nothing.

Usage (run from the project root):
    python -m backend.backfill_sc_mc_scores --dry-run
    python -m backend.backfill_sc_mc_scores --yes
"""

import argparse
import os

from dotenv import load_dotenv

_root = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(os.path.dirname(_root), ".env"))

from backend.database import SessionLocal
from backend.models import BenchmarkOutput, BenchmarkTask
from backend.processing.pipeline import score_sc_mc_percent


def find_mismatches(db):
    """Return [(BenchmarkOutput, question_id, gold_answer, recomputed_score), ...]."""
    rows = (
        db.query(BenchmarkOutput, BenchmarkTask.question_id, BenchmarkTask.gold_answer)
        .join(BenchmarkTask, BenchmarkTask.id == BenchmarkOutput.task_id)
        .filter(BenchmarkOutput.evaluation_method == "sc_mc_formula")
        .all()
    )
    mismatches = []
    for output, qid, gold in rows:
        recomputed = score_sc_mc_percent(output.final_answer, gold)
        stored = output.score_percent_sc_mc or 0.0
        if abs(recomputed - stored) > 0.01:
            mismatches.append((output, qid, gold, recomputed))
    return mismatches


def main():
    parser = argparse.ArgumentParser(description="Recompute stale SC/MC formula scores.")
    parser.add_argument("--dry-run", action="store_true", help="Print what would change, no writes")
    parser.add_argument("--yes", action="store_true", help="Skip the interactive confirmation prompt")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        mismatches = find_mismatches(db)
        if not mismatches:
            print("No stale SC/MC scores found — nothing to do.")
            return

        task_qids = {qid for _, qid, _, _ in mismatches}
        print(f"Found {len(mismatches)} row(s) across {len(task_qids)} task(s) with stale scores:\n")
        for output, qid, gold, recomputed in mismatches:
            print(
                f"  {qid} / {output.model_name}  "
                f"final_answer={output.final_answer!r}  gold={gold!r}  "
                f"stored={output.score_percent_sc_mc}  ->  recomputed={recomputed}"
            )

        if args.dry_run:
            print("\n--dry-run: no changes made.")
            return

        if not args.yes:
            confirm = input("\nType 'yes' to apply these corrections: ").strip().lower()
            if confirm != "yes":
                print("Aborted — nothing changed.")
                return

        for output, qid, gold, recomputed in mismatches:
            output.score_percent_sc_mc = recomputed
            output.final_score_percent = recomputed
        db.commit()

        print(f"\nUpdated {len(mismatches)} row(s).")

    finally:
        db.close()


if __name__ == "__main__":
    main()
