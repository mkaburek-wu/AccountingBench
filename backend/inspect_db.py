import sqlite3, sys

conn = sqlite3.connect("backend/accountingbench.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

task_id = int(sys.argv[1]) if len(sys.argv) > 1 else 19

cur.execute("SELECT * FROM benchmark_tasks WHERE id = ?", (task_id,))
row = cur.fetchone()
if row:
    print(f"=== benchmark_tasks id={task_id} ===")
    for key in row.keys():
        val = row[key]
        if val is None:
            continue
        if isinstance(val, str) and len(val) > 200:
            print(f"\n{key}:\n{val[:3000]}{'...[truncated]' if len(val) > 3000 else ''}")
        else:
            print(f"{key}: {val}")

# Also show the run record for alawyer on this task
cur.execute("""
    SELECT * FROM benchmark_runs
    WHERE task_id = ? AND model_name LIKE '%awyer%'
""", (task_id,))
runs = cur.fetchall()
print(f"\n=== benchmark_runs for task {task_id} / alawyer ===")
for r in runs:
    for key in r.keys():
        val = r[key]
        if val is None:
            continue
        if isinstance(val, str) and len(val) > 200:
            print(f"\n{key}:\n{val[:2000]}")
        else:
            print(f"{key}: {val}")

conn.close()
