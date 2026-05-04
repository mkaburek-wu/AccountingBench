import sqlite3
import pandas as pd

conn = sqlite3.connect("accountingbench.db")

# Export a specific table
df = pd.read_sql_query("SELECT * FROM benchmark_outputs", conn)
df.to_excel("output.xlsx", index=False)

# Export multiple tables to separate sheets
with pd.ExcelWriter("output.xlsx") as writer:
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    for (table_name,) in tables:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        df.to_excel(writer, sheet_name=table_name, index=False)

conn.close()