"""
AccountingBench — Deduplicate benchmark_outputs
=================================================
Historically, rerun_model.py could reprocess models that already had
results for a task (see backend/rerun_model.py process_task() — fixed
separately), leaving duplicate benchmark_outputs rows for the same
(task_id, model_name) pair, each with its own benchmark_runs row.

This script finds every such duplicate pair, keeps the EARLIEST
evaluated_at_utc row (and its matching benchmark_runs row, via run_id),
and deletes the later one(s). It also cleans up orphaned benchmark_runs
rows left behind by abandoned/failed attempts (a run row with no
matching benchmark_outputs row, alongside a sibling run row for the
same task+model that does have one). Safe to run multiple times — a
clean DB reports zero duplicates and does nothing.

Usage (run from the project root):
    python -m backend.dedup_outputs --dry-run
    python -m backend.dedup_outputs
"""

import argparse
from collections import defaultdict

from dotenv import load_dotenv
import os

_root = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(os.path.dirname(_root), ".env"))

from backend.database import SessionLocal
from backend.models import BenchmarkOutput, BenchmarkRun, BenchmarkTask


def find_duplicate_groups(db):
    """Return {(task_id, model_name): [BenchmarkOutput, ...]} for every pair with >1 row."""
    rows = db.query(BenchmarkOutput).order_by(BenchmarkOutput.evaluated_at_utc).all()
    groups = defaultdict(list)
    for r in rows:
        groups[(r.task_id, r.model_name)].append(r)
    return {k: v for k, v in groups.items() if len(v) > 1}


def find_orphaned_runs(db):
    """
    Return BenchmarkRun rows that duplicate a (task_id, model_name) pair but
    whose run_id has no matching benchmark_outputs row — leftovers from an
    abandoned/failed attempt, once a sibling run for the same pair completed
    successfully. Only pairs with exactly one matching output are handled;
    anything else is left alone and reported so it can be reviewed by hand.
    """
    run_rows = db.query(BenchmarkRun).all()
    groups = defaultdict(list)
    for r in run_rows:
        groups[(r.task_id, r.model_name)].append(r)
    dupe_groups = {k: v for k, v in groups.items() if len(v) > 1}

    orphans, unresolved = [], []
    for (task_id, model_name), runs in dupe_groups.items():
        output_run_ids = {
            o.run_id for o in db.query(BenchmarkOutput.run_id)
            .filter_by(task_id=task_id, model_name=model_name).all()
        }
        if len(output_run_ids) != 1:
            unresolved.append((task_id, model_name, runs, output_run_ids))
            continue
        keep_run_id = next(iter(output_run_ids))
        orphans.extend(r for r in runs if r.run_id != keep_run_id)
    return orphans, unresolved


def main():
    parser = argparse.ArgumentParser(description="Deduplicate benchmark_outputs rows.")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be deleted, no writes")
    parser.add_argument("--yes", action="store_true", help="Skip the interactive confirmation prompt")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        dupes = find_duplicate_groups(db)
        orphan_runs, unresolved = find_orphaned_runs(db)

        if not dupes and not orphan_runs:
            print("No duplicate (task_id, model_name) pairs found — nothing to do.")
            if unresolved:
                _print_unresolved(unresolved)
            return

        task_ids = {tid for tid, _ in dupes} | {r.task_id for r in orphan_runs}
        qid_by_tid = {
            t.id: t.question_id
            for t in db.query(BenchmarkTask).filter(BenchmarkTask.id.in_(task_ids)).all()
        }

        output_ids_to_delete = []
        run_keys_to_delete = []  # (task_id, model_name, run_id) — run_id alone is shared across models

        if dupes:
            print(f"Found {len(dupes)} duplicate (task_id, model_name) pair(s) in benchmark_outputs:\n")
            for (task_id, model_name), rows in sorted(dupes.items()):
                keep, *drop = rows  # earliest first (query is ordered by evaluated_at_utc)
                qid = qid_by_tid.get(task_id, f"task_id={task_id}")
                print(f"  {qid} / {model_name}")
                print(f"    KEEP   {keep.evaluated_at_utc}  score={keep.final_score_percent}  run_id={keep.run_id}")
                for d in drop:
                    print(f"    DELETE {d.evaluated_at_utc}  score={d.final_score_percent}  run_id={d.run_id}")
                    output_ids_to_delete.append(d.id)
                    run_keys_to_delete.append((task_id, model_name, d.run_id))

        if orphan_runs:
            print(f"\nFound {len(orphan_runs)} orphaned benchmark_runs row(s) "
                  f"(abandoned attempt, no matching output):\n")
            for r in orphan_runs:
                qid = qid_by_tid.get(r.task_id, f"task_id={r.task_id}")
                print(f"  {qid} / {r.model_name}  DELETE run_id={r.run_id}  ({r.run_timestamp})")
                run_keys_to_delete.append((r.task_id, r.model_name, r.run_id))

        if unresolved:
            _print_unresolved(unresolved)

        print(f"\nThis will delete {len(output_ids_to_delete)} benchmark_outputs row(s)"
              f" and {len(run_keys_to_delete)} benchmark_runs row(s).")

        if args.dry_run:
            print("\n--dry-run: no changes made.")
            return

        if not args.yes:
            confirm = input("\nType 'yes' to confirm deletion: ").strip().lower()
            if confirm != "yes":
                print("Aborted — nothing deleted.")
                return

        db.query(BenchmarkOutput).filter(BenchmarkOutput.id.in_(output_ids_to_delete)).delete(synchronize_session=False)

        run_deleted = 0
        for task_id, model_name, run_id in run_keys_to_delete:
            # run_id is shared across all models processed together in one run_pipeline()
            # call — filter by (task_id, model_name, run_id) so we only remove the
            # BenchmarkRun row for THIS model, not sibling models sharing the same run_id.
            run_deleted += (
                db.query(BenchmarkRun)
                .filter_by(task_id=task_id, model_name=model_name, run_id=run_id)
                .delete(synchronize_session=False)
            )
        db.commit()

        print(f"\nDeleted {len(output_ids_to_delete)} benchmark_outputs row(s) "
              f"and {run_deleted} benchmark_runs row(s).")

    finally:
        db.close()


def _print_unresolved(unresolved):
    print(f"\n{len(unresolved)} (task_id, model_name) pair(s) in benchmark_runs have duplicate rows "
          f"but not exactly one matching output — left untouched, review manually:")
    for task_id, model_name, runs, output_run_ids in unresolved:
        print(f"  task_id={task_id} model={model_name}  "
              f"run_ids={[r.run_id for r in runs]}  matching_output_run_ids={sorted(output_run_ids)}")


if __name__ == "__main__":
    main()
