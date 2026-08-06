"""
AccountingBench — Split options that swallowed a later option
=============================================================
parse_options() (backend/batch_run.py) only treats "X)" as a new option at the
START of a line. When the source sheet puts two options on one line, the second
is absorbed into the first one's TEXT: the swallowed letter never becomes a key,
so pipeline.py derives valid_choices without it and every model answer naming
that letter is rejected.

Concrete case — task 1304 (12015528_0041):

    "B": "Eine Aufwertung auf den hoeheren Verkehrswert ist verpflichtend zu
          erfassen. C) Eine Aufwertung auf den hoeheren Verkehrswert ist erlaubt."

Option C exists in the prompt the models were shown, and 10 of them answered C,
but options has no C key and gold_answer is "C,D" — so the task was unwinnable.

This script splits such values back apart. It is deliberately conservative: a
task is only rewritten when every check below passes, so it can never invent an
option that was not really there.

  1. the buried letter is not already a key
  2. the buried letter currently sits in a GAP in the letter sequence
  3. both halves of the split are non-empty
  4. the resulting keys form one contiguous run A..N with no gaps

Detection uses the same regex as check_field_consistency() in batch_utils.py,
so what --dry-run reports there is exactly what this repairs.

Pure data fix — no API calls. It does NOT touch benchmark_outputs: answers
already stored for a repaired task were produced from the malformed prompt and
should be re-run, not re-scored (see the note this prints at the end).

Usage (run from the project root):
    python -m backend.fix_buried_options                      # report candidates
    python -m backend.fix_buried_options --task-ids 1304 --dry-run
    python -m backend.fix_buried_options --task-ids 1304 --yes
"""

import argparse
import os
import re

from dotenv import load_dotenv

_root = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(os.path.dirname(_root), ".env"))

from backend.database import SessionLocal
from backend.models import BenchmarkTask, BenchmarkOutput

# Same pattern check_field_consistency() uses to raise its OPTS warning.
BURIED_RE = re.compile(r"(?<![A-Za-z0-9])([A-Za-z])\)\s")


def letters_of(opts):
    return sorted(str(k).strip().upper() for k in opts if len(str(k).strip()) == 1)


def gaps_in(letters):
    if len(letters) < 2:
        return []
    span = [chr(c) for c in range(ord(letters[0]), ord(letters[-1]) + 1)]
    return [c for c in span if c not in letters]


def plan_split(opts):
    """Return (new_opts, [description]) or (None, [reason]) if not safely fixable."""
    if not isinstance(opts, dict) or list(opts.keys()) == ["raw"]:
        return None, ["options are not a parsed dict"]

    keys = {str(k).strip().upper() for k in opts}
    missing = set(gaps_in(letters_of(opts)))
    if not missing:
        return None, ["no gap in the letter sequence — nothing was swallowed"]

    new_opts = {str(k).strip().upper(): v for k, v in opts.items()}
    notes = []

    for key in list(new_opts):
        value = new_opts[key]
        if not isinstance(value, str):
            continue
        m = BURIED_RE.search(value)
        if not m:
            continue
        buried = m.group(1).upper()

        if buried in keys:
            notes.append(f"option {key}: found {buried!r} but it is already a key — skipped")
            continue
        if buried not in missing:
            notes.append(f"option {key}: found {buried!r} but it does not fill a gap — skipped")
            continue

        head = value[: m.start()].strip()
        tail = value[m.end():].strip()
        if not head or not tail:
            notes.append(f"option {key}: split at {buried!r} would leave an empty half — skipped")
            continue

        new_opts[key] = head
        new_opts[buried] = tail
        keys.add(buried)
        missing.discard(buried)
        notes.append(f"option {key} split at {buried!r})  ->  {key} + {buried}")

    if new_opts == {str(k).strip().upper(): v for k, v in opts.items()}:
        return None, notes or ["no buried marker found"]

    remaining = gaps_in(letters_of(new_opts))
    if remaining:
        return None, notes + [f"REJECTED: letters still have gap(s) {remaining} after the split"]

    return {k: new_opts[k] for k in sorted(new_opts)}, notes


def main():
    ap = argparse.ArgumentParser(description="Split options that absorbed a later option.")
    ap.add_argument("--task-ids", help="Comma-separated benchmark_tasks.id values to repair")
    ap.add_argument("--dry-run", action="store_true", help="Show the change, write nothing")
    ap.add_argument("--yes", action="store_true", help="Skip the interactive confirmation")
    args = ap.parse_args()

    db = SessionLocal()
    try:
        q = db.query(BenchmarkTask).filter(
            BenchmarkTask.answer_type.in_(["single_choice", "multi_choice"]),
            BenchmarkTask.options.isnot(None),
        )
        if args.task_ids:
            ids = [int(x) for x in args.task_ids.split(",") if x.strip()]
            q = q.filter(BenchmarkTask.id.in_(ids))
        tasks = q.all()

        if not args.task_ids:
            print("No --task-ids given — reporting candidates only.\n")
            found = 0
            for t in tasks:
                new_opts, notes = plan_split(t.options)
                if new_opts:
                    found += 1
                    print(f"  CANDIDATE  task {t.id:5} {t.question_id:16} "
                          f"{letters_of(t.options)} -> {letters_of(new_opts)}")
            print(f"\n{found} task(s) could be repaired. Re-run with "
                  f"--task-ids <id[,id...]> --dry-run to inspect one.")
            return

        changed = []
        for t in tasks:
            print(f"\n=== task {t.id}  {t.question_id} ===")
            print(f"  answer_type : {t.answer_type}")
            print(f"  gold_answer : {t.gold_answer!r}")
            print(f"  letters now : {letters_of(t.options)}  gaps={gaps_in(letters_of(t.options))}")

            new_opts, notes = plan_split(t.options)
            for n in notes:
                print(f"    - {n}")
            if not new_opts:
                print("  NOT FIXABLE — left unchanged.")
                continue

            print(f"  letters after: {letters_of(new_opts)}  gaps={gaps_in(letters_of(new_opts))}")
            print("  new options:")
            for k in sorted(new_opts):
                print(f"    {k}: {new_opts[k]}")

            gold = {c.strip().upper() for c in re.split(r"[,\s]+", t.gold_answer or "") if c.strip()}
            unsatisfiable = gold - set(letters_of(new_opts))
            print(f"  gold {sorted(gold)} satisfiable: "
                  f"{'YES' if not unsatisfiable else f'NO — still missing {sorted(unsatisfiable)}'}")

            n_out = db.query(BenchmarkOutput).filter_by(task_id=t.id).count()
            print(f"  existing outputs on this task: {n_out} "
                  f"(NOT modified — they answered a malformed prompt and need a re-run)")
            changed.append((t, new_opts))

        if not changed:
            print("\nNothing to change.")
            return
        if args.dry_run:
            print("\n--dry-run: no changes made.")
            return
        if not args.yes:
            if input("\nType 'yes' to apply: ").strip().lower() != "yes":
                print("Aborted — nothing changed.")
                return

        for t, new_opts in changed:
            t.options = new_opts
        db.commit()
        print(f"\nUpdated {len(changed)} task(s).")
        print("\nNOTE: benchmark_outputs for these tasks were left untouched on purpose.")
        print("Those answers were produced from the malformed option list, so re-scoring")
        print("them would credit answers given to a different prompt. Delete and re-run")
        print("the affected (task, model) pairs when you want clean scores.")

    finally:
        db.close()


if __name__ == "__main__":
    main()
