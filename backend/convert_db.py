import argparse
import datetime
import sqlite3

import pandas as pd

parser = argparse.ArgumentParser(description="Export accountingbench.db to an Excel workbook.")
parser.add_argument("-a", "--public-only", action="store_true",
                     help="Only export tasks/outputs/runs where benchmark_tasks.is_public = 1")
args = parser.parse_args()

conn = sqlite3.connect("accountingbench.db")

public_task_ids = None
if args.public_only:
    public_task_ids = pd.read_sql_query(
        "SELECT id FROM benchmark_tasks WHERE is_public = 1", conn
    )["id"].tolist()

out_file = (
    f"output_public_{datetime.date.today().isoformat()}.xlsx"
    if args.public_only else "output.xlsx"
)

# Export all tables to separate sheets
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
with pd.ExcelWriter(out_file) as writer:
    for (table_name,) in tables:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        if args.public_only:
            if table_name == "benchmark_tasks":
                df = df[df["is_public"] == 1]
            elif table_name in ("benchmark_outputs", "benchmark_runs"):
                df = df[df["task_id"].isin(public_task_ids)]
        df.to_excel(writer, sheet_name=table_name, index=False)

conn.close()
print(f"Wrote {out_file}")
