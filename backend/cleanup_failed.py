"""
AccountingBench — Clean up fully-failed tasks
==============================================
Deletes benchmark_tasks (and all related rows) where every submission
has status='error' and no 'done' submission exists.  Safe to run any
time — tasks with at least one successful submission are never touched.

Usage (run from the project root):
    python -m backend.cleanup_failed
"""

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv
load_dotenv(_ROOT / ".env", override=False)

from backend.database import SessionLocal
from backend.models import BenchmarkTask, BenchmarkOutput, BenchmarkRun, Submission


def main() -> None:
    db = SessionLocal()
    try:
        # Tasks that have at least one error submission and NO done submission
        error_task_ids = (
            db.query(Submission.task_id)
            .filter(Submission.status == "error")
            .filter(
                ~db.query(Submission.task_id)
                .filter(Submission.status == "done")
                .correlate(Submission)
                .exists()
            )
            .distinct()
            .all()
        )

        # Simpler: build the set in Python — avoids complex correlated subquery
        done_task_ids  = {r[0] for r in db.query(Submission.task_id)
                                          .filter(Submission.status == "done").all()}
        error_task_ids = {r[0] for r in db.query(Submission.task_id)
                                          .filter(Submission.status == "error").all()}
        to_delete = error_task_ids - done_task_ids

        if not to_delete:
            print("No fully-failed tasks found — nothing to delete.")
            return

        tasks = (
            db.query(BenchmarkTask)
            .filter(BenchmarkTask.id.in_(to_delete))
            .order_by(BenchmarkTask.question_id)
            .all()
        )

        print(f"\nFound {len(tasks)} fully-failed task(s):\n")
        for t in tasks:
            print(f"  {t.question_id}  (id={t.id})")

        print(f"\nThis will delete:")
        output_count = db.query(BenchmarkOutput).filter(BenchmarkOutput.task_id.in_(to_delete)).count()
        run_count    = db.query(BenchmarkRun).filter(BenchmarkRun.task_id.in_(to_delete)).count()
        sub_count    = db.query(Submission).filter(Submission.task_id.in_(to_delete)).count()
        print(f"  {output_count} benchmark_outputs row(s)")
        print(f"  {run_count} benchmark_runs row(s)")
        print(f"  {sub_count} submissions row(s)")
        print(f"  {len(tasks)} benchmark_tasks row(s)")

        confirm = input("\nType 'yes' to confirm deletion: ").strip().lower()
        if confirm != "yes":
            print("Aborted — nothing deleted.")
            return

        # Delete in FK-safe order
        db.query(BenchmarkOutput).filter(BenchmarkOutput.task_id.in_(to_delete)).delete(synchronize_session=False)
        db.query(BenchmarkRun).filter(BenchmarkRun.task_id.in_(to_delete)).delete(synchronize_session=False)
        db.query(Submission).filter(Submission.task_id.in_(to_delete)).delete(synchronize_session=False)
        db.query(BenchmarkTask).filter(BenchmarkTask.id.in_(to_delete)).delete(synchronize_session=False)
        db.commit()

        print(f"\nDeleted {len(tasks)} task(s). You can now rerun them with batch_run.py.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
