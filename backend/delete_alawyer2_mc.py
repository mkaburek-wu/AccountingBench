"""
Delete alawyer2 benchmark_outputs for multi_choice tasks so they can be re-run.

Usage:
    python -m backend.delete_alawyer2_mc          # dry run — shows what would be deleted
    python -m backend.delete_alawyer2_mc --confirm # actually deletes
"""

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv
load_dotenv(dotenv_path=_ROOT / ".env", override=False)

from backend.database import SessionLocal
from backend.models import BenchmarkOutput, BenchmarkTask

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--confirm", action="store_true",
                        help="Actually delete. Without this flag the script is a dry run.")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        rows = (
            db.query(BenchmarkOutput)
            .join(BenchmarkTask, BenchmarkTask.id == BenchmarkOutput.task_id)
            .filter(
                BenchmarkOutput.model_name == "alawyer2",
                BenchmarkTask.answer_type == "multi_choice",
            )
            .all()
        )

        print(f"Found {len(rows)} alawyer2 multi_choice output(s) to delete:")
        for r in rows:
            print(f"  output_id={r.id}  task_id={r.task_id}  final={repr(r.final_answer)[:40]}  score={r.final_score_percent}")

        if not args.confirm:
            print("\nDry run — nothing deleted. Re-run with --confirm to delete.")
            return

        for r in rows:
            db.delete(r)
        db.commit()
        print(f"\nDeleted {len(rows)} row(s). Now re-run with:")
        print('  python -m backend.rerun_model --models "alawyer2" --answer-type "multi_choice" --max-workers 1')

    finally:
        db.close()

if __name__ == "__main__":
    main()
