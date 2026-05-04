import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "backend" / "accountingbench.db"

def reset_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    tables = ["benchmark_outputs", "benchmark_runs", "submissions", "benchmark_tasks"]

    print("Deleting data...")
    for table in tables:
        cur.execute(f"DELETE FROM {table}")
        print(f"  ✓ {table}: {cur.rowcount} rows deleted")

    print("Resetting auto-increment IDs...")
    try:
        for table in tables:
            cur.execute("DELETE FROM sqlite_sequence WHERE name = ?", (table,))
        print("  ✓ IDs reset")
    except sqlite3.OperationalError:
        print("  ℹ No sqlite_sequence table found — IDs will reset naturally on next insert")

    conn.commit()
    conn.close()

    print("\nDone. Database reset complete.")

if __name__ == "__main__":
    confirm = input(f"Reset database at {DB_PATH}? This cannot be undone. (yes/no): ")
    if confirm.strip().lower() == "yes":
        reset_db()
    else:
        print("Aborted.")