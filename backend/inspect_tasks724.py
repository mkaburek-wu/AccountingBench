import sqlite3

conn = sqlite3.connect("backend/accountingbench.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Check task IDs 724-729 with alawyer2 outputs
cur.execute("""
    SELECT t.id, t.question_id, t.answer_type, t.gold_answer,
           o.model_answer_1, o.model_answer_2, o.model_answer_3,
           o.final_answer, o.final_score_percent, o.evaluation_notes
    FROM benchmark_tasks t
    LEFT JOIN benchmark_outputs o ON o.task_id = t.id AND o.model_name = 'alawyer2'
    WHERE t.id BETWEEN 724 AND 729
    ORDER BY t.id
""")
rows = cur.fetchall()
print("Tasks 724-729 with alawyer2 outputs:")
for r in rows:
    print(f"  task_id={r['id']} qid={r['question_id']} type={r['answer_type']}")
    print(f"    gold={repr(r['gold_answer'])[:60]}")
    print(f"    a1={repr(r['model_answer_1'])[:60]}")
    print(f"    final={repr(r['final_answer'])[:60]}  score={r['final_score_percent']}")
    print(f"    notes={repr(r['evaluation_notes'])[:80]}")
    print()

# Also check if they might be row numbers in a different table
cur.execute("SELECT MIN(id), MAX(id) FROM benchmark_tasks")
row = cur.fetchone()
print(f"\nbenchmark_tasks ID range: {row[0]} to {row[1]}")

cur.execute("SELECT MIN(id), MAX(id) FROM benchmark_outputs WHERE model_name = 'alawyer2'")
row = cur.fetchone()
print(f"alawyer2 output ID range: {row[0]} to {row[1]}")

conn.close()
