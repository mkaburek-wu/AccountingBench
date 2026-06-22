import sqlite3

conn = sqlite3.connect("backend/accountingbench.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Answer type breakdown
cur.execute("""
    SELECT t.answer_type, COUNT(*) as n,
           ROUND(AVG(o.final_score_percent), 1) as avg_score
    FROM benchmark_outputs o
    LEFT JOIN benchmark_tasks t ON t.id = o.task_id
    WHERE o.model_name = 'alawyer2'
    GROUP BY t.answer_type
""")
print("== Score by answer_type ==")
for r in cur.fetchall():
    print(f"  {r['answer_type']:<20} n={r['n']}  avg={r['avg_score']}%")

# Multi-choice: show all 3 trials to see if they vary
cur.execute("""
    SELECT o.id, t.question_id,
           o.model_answer_1, o.model_answer_2, o.model_answer_3,
           o.final_answer, o.final_score_percent
    FROM benchmark_outputs o
    LEFT JOIN benchmark_tasks t ON t.id = o.task_id
    WHERE o.model_name = 'alawyer2'
      AND t.answer_type = 'multi_choice'
    ORDER BY o.id
    LIMIT 10
""")
print("\n== Multi-choice: 3 trials per task ==")
for r in cur.fetchall():
    print(f"  qid={r['question_id']}  a1={r['model_answer_1']!r}  a2={r['model_answer_2']!r}  a3={r['model_answer_3']!r}  final={r['final_answer']!r}  score={r['final_score_percent']}")

# Single-choice stats
cur.execute("""
    SELECT COUNT(*) FROM benchmark_outputs o
    LEFT JOIN benchmark_tasks t ON t.id = o.task_id
    WHERE o.model_name = 'alawyer2' AND t.answer_type = 'single_choice'
""")
sc_count = cur.fetchone()[0]
print(f"\n== Single-choice tasks: {sc_count} ==")
if sc_count:
    cur.execute("""
        SELECT o.final_answer, o.final_score_percent
        FROM benchmark_outputs o
        LEFT JOIN benchmark_tasks t ON t.id = o.task_id
        WHERE o.model_name = 'alawyer2' AND t.answer_type = 'single_choice'
        LIMIT 10
    """)
    for r in cur.fetchall():
        print(f"  final={r['final_answer']!r}  score={r['final_score_percent']}")

conn.close()
