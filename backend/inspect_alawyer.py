import sqlite3, re
from collections import defaultdict

conn = sqlite3.connect("backend/accountingbench.db")
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("""
    SELECT
        o.id, o.task_id,
        o.model_answer_1, o.model_answer_2, o.model_answer_3,
        o.final_answer,
        o.final_score_percent,
        o.judge_score_percent,
        o.score_percent_sc_mc,
        o.evaluation_method,
        o.evaluation_notes,
        t.answer_type, t.category, t.subcategory, t.question_id
    FROM benchmark_outputs o
    LEFT JOIN benchmark_tasks t ON t.id = o.task_id
    WHERE o.model_name = 'alawyer'
      AND o.id BETWEEN 1518 AND 1670
    ORDER BY o.id
""")
rows = cur.fetchall()
conn.close()

# ── Filters ────────────────────────────────────────────────────────────────────
def is_pv(r):
    return (r["question_id"] or "").startswith("12008933") or \
           "personalverrechnung" in (r["subcategory"] or "").lower()

def has_error(r):
    fa = r["final_answer"] or ""
    a1 = r["model_answer_1"] or ""
    a2 = r["model_answer_2"] or ""
    a3 = r["model_answer_3"] or ""
    notes = r["evaluation_notes"] or ""

    corrupt = re.compile(r'Ã[¤öüÄÖÜ¶¼½¾]|â€[œ"™]|Ã‚|â€"|â€˜|â€™')
    if any(corrupt.search(t) for t in [fa, a1, a2, a3]):
        return True
    if not fa.strip():
        return True
    if (fa.strip().startswith("{") and ":" in fa) or \
       (a1.strip().startswith("{") and ":" in a1):
        return True
    if any(p in notes.lower() for p in
           ["bricht ab", "abgebrochen", "fehlen bzw", "wurden nicht beantwortet"]):
        return True
    return False

# ── Build the four subsets ─────────────────────────────────────────────────────
all_rows        = rows
excl_pv         = [r for r in rows if not is_pv(r)]
excl_err        = [r for r in rows if not has_error(r)]
excl_pv_and_err = [r for r in rows if not is_pv(r) and not has_error(r)]

# ── Stats helper ───────────────────────────────────────────────────────────────
def agg(row_list):
    scores = [r["final_score_percent"] for r in row_list if r["final_score_percent"] is not None]
    judge  = [r["judge_score_percent"]  for r in row_list if r["judge_score_percent"]  is not None]
    scmc   = [r["score_percent_sc_mc"]  for r in row_list if r["score_percent_sc_mc"]  is not None]
    by_type = defaultdict(list)
    for r in row_list:
        at = r["answer_type"] or "unknown"
        if r["final_score_percent"] is not None:
            by_type[at].append(r["final_score_percent"])
    return {
        "n":       len(row_list),
        "overall": sum(scores)/len(scores) if scores else None,
        "judge":   sum(judge)/len(judge)   if judge  else None,
        "scmc":    sum(scmc)/len(scmc)     if scmc   else None,
        "sc_n":    len(by_type.get("single_choice", [])),
        "mc_n":    len(by_type.get("multi_choice",  [])),
        "ot_n":    len(by_type.get("open_text",     [])),
        "sc_avg":  sum(by_type["single_choice"])/len(by_type["single_choice"]) if by_type["single_choice"] else None,
        "mc_avg":  sum(by_type["multi_choice"]) /len(by_type["multi_choice"])  if by_type["multi_choice"]  else None,
        "ot_avg":  sum(by_type["open_text"])    /len(by_type["open_text"])     if by_type["open_text"]     else None,
    }

A = agg(all_rows)
B = agg(excl_pv)
C = agg(excl_err)
D = agg(excl_pv_and_err)

def pct(v): return f"{v:.1f}%" if v is not None else "—"
def row_fmt(label, va, vb, vc, vd):
    print(f"  {label:<28} {pct(va):>8}  {pct(vb):>15}  {pct(vc):>12}  {pct(vd):>20}")

# ── Print comparison table ─────────────────────────────────────────────────────
COL1 = f"All ({A['n']})"
COL2 = f"Excl. PV ({B['n']})"
COL3 = f"Excl. errors ({C['n']})"
COL4 = f"Excl. PV + errors ({D['n']})"

header = f"  {'Metric':<28} {COL1:>8}  {COL2:>15}  {COL3:>12}  {COL4:>20}"
print(header)
print("  " + "-" * (len(header) - 2))

row_fmt("Overall avg",          A["overall"], B["overall"], C["overall"], D["overall"])
row_fmt("Judge avg (open_text)", A["judge"],   B["judge"],   C["judge"],   D["judge"])
row_fmt("SC/MC avg",            A["scmc"],    B["scmc"],    C["scmc"],    D["scmc"])
print()
row_fmt(f"single_choice  (n={A['sc_n']}/{B['sc_n']}/{C['sc_n']}/{D['sc_n']})",
        A["sc_avg"], B["sc_avg"], C["sc_avg"], D["sc_avg"])
row_fmt(f"multi_choice   (n={A['mc_n']}/{B['mc_n']}/{C['mc_n']}/{D['mc_n']})",
        A["mc_avg"], B["mc_avg"], C["mc_avg"], D["mc_avg"])
row_fmt(f"open_text      (n={A['ot_n']}/{B['ot_n']}/{C['ot_n']}/{D['ot_n']})",
        A["ot_avg"], B["ot_avg"], C["ot_avg"], D["ot_avg"])

print(f"\nExclusion counts:")
print(f"  Personalverrechnung tasks : {sum(1 for r in rows if is_pv(r))}")
print(f"  Tasks with errors         : {sum(1 for r in rows if has_error(r))}")
print(f"  Both (overlap)            : {sum(1 for r in rows if is_pv(r) and has_error(r))}")
print(f"  Total excluded (union)    : {len(rows) - len(excl_pv_and_err)}")
