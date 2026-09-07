import argparse
import datetime
import os
import sqlite3

import pandas as pd

parser = argparse.ArgumentParser(description="Export accountingbench.db to an Excel workbook.")
parser.add_argument("-a", "--public-only", action="store_true",
                     help="Only export tasks/outputs/runs where benchmark_tasks.is_public = 1")
parser.add_argument(
    "--question-ids", default=None, dest="question_ids",
    help=(
        "Filter tasks by question_id. Comma-separated tokens, each of which can be:\n"
        "  exact   — '11908783_0028'\n"
        "  prefix  — '11908783'  (matches all 11908783_* tasks)\n"
        "  range   — '11908783_0001:11908783_0050'  (inclusive, lexicographic)"
    ),
)
args = parser.parse_args()


def _parse_question_ids(raw: str | None) -> list[dict] | None:
    """Parse --question-ids into a list of filter specs (same convention as rerun_model.py).

    Each comma-separated token becomes one dict:
      {"type": "exact",  "value": "11908783_0028"}
      {"type": "prefix", "value": "11908783"}
      {"type": "range",  "start": "11908783_0001", "end": "11908783_0050"}
    """
    if not raw:
        return None
    specs = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        if ":" in token:
            start, end = token.split(":", 1)
            specs.append({"type": "range", "start": start.strip(), "end": end.strip()})
        elif "_" not in token:
            specs.append({"type": "prefix", "value": token})
        else:
            specs.append({"type": "exact", "value": token})
    return specs or None


def _qid_mask(question_id: pd.Series, specs: list[dict]) -> pd.Series:
    """Build an OR mask over a question_id column from _parse_question_ids specs."""
    mask = pd.Series(False, index=question_id.index)
    for spec in specs:
        if spec["type"] == "exact":
            mask |= question_id == spec["value"]
        elif spec["type"] == "prefix":
            mask |= question_id.str.startswith(spec["value"] + "_")
        elif spec["type"] == "range":
            mask |= (question_id >= spec["start"]) & (question_id <= spec["end"])
    return mask


qid_specs = _parse_question_ids(args.question_ids)

conn = sqlite3.connect("accountingbench.db")

task_ids_filter = None
if args.public_only or qid_specs:
    tasks = pd.read_sql_query("SELECT id, question_id, is_public FROM benchmark_tasks", conn)
    mask = pd.Series(True, index=tasks.index)
    if args.public_only:
        mask &= tasks["is_public"] == 1
    if qid_specs:
        mask &= _qid_mask(tasks["question_id"], qid_specs)
    task_ids_filter = tasks.loc[mask, "id"].tolist()
    if qid_specs and not task_ids_filter:
        conn.close()
        raise SystemExit(f"No task matches --question-ids {args.question_ids!r}"
                          + (" that is also is_public=1" if args.public_only else ""))

output_dir = "output"
os.makedirs(output_dir, exist_ok=True)
name_parts = ["output"]
if args.public_only:
    name_parts.append("public")
if args.question_ids:
    tag = args.question_ids.replace(",", "-").replace(":", "-")[:60]
    name_parts.append(tag)
if args.public_only:
    name_parts.append(datetime.date.today().isoformat())
out_file = os.path.join(output_dir, "_".join(name_parts) + ".xlsx")

# Export all tables to separate sheets
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
with pd.ExcelWriter(out_file) as writer:
    for (table_name,) in tables:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        if task_ids_filter is not None:
            if table_name == "benchmark_tasks":
                df = df[df["id"].isin(task_ids_filter)]
            elif table_name in ("benchmark_outputs", "benchmark_runs"):
                df = df[df["task_id"].isin(task_ids_filter)]
        df.to_excel(writer, sheet_name=table_name, index=False)

conn.close()
print(f"Wrote {out_file}")
