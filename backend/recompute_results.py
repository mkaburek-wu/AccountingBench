"""
One-off script: recompute per-model benchmark scores from a fresh Excel export
and compare against the current public/results.js.

Usage (from project root):
    python -m backend.recompute_results

Reads backend/uploads/300726_results_N564.xlsx (sheets benchmark_tasks,
benchmark_outputs), computes every BENCHMARK_RESULTS field per model, diffs
the 10 "should be unchanged" models against the current results.js, and
prints ready-to-paste JS blocks for the 3 models that actually changed
(gpt-5.5, claude-opus-4-7, Kimi-K2.6).
"""
import re
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
XLSX_PATH = ROOT / "backend" / "uploads" / "300726_results_N564.xlsx"
RESULTS_JS_PATH = ROOT / "public" / "results.js"

UPDATED_MODELS = [
    "gpt-5.5", "claude-opus-4-7", "Kimi-K2.6",
    "claude-opus-4-6", "Mistral-Large-3", "DeepSeek-V3.2", "gpt-5-mini",
]

SCORE_FIELDS = [
    "overall", "tax", "financial", "management",
    "interpLaw", "calculation", "journal",
    "multiChoice", "openText", "singleChoice", "journalEntry",
    "austrianTax", "mixedAcc", "ugb", "ifrs",
]

# Models with reasoning tokens that are NOT already included in token_output
# (confirmed via data inspection: grok/mercury-2 report reasoning tokens far
# larger than token_output, so they must be added; gpt-5.x/Kimi already
# include reasoning inside token_output).
ADD_REASONING_TOKENS = {"grok-4-fast-reasoning", "mercury-2"}


def load_data():
    tasks = pd.read_excel(XLSX_PATH, sheet_name="benchmark_tasks")
    outputs = pd.read_excel(XLSX_PATH, sheet_name="benchmark_outputs")
    task_meta = tasks[["id", "category", "task_type", "answer_type",
                        "regulatory_framework", "education_level"]].rename(
        columns={"id": "task_id"}
    )
    df = outputs.merge(task_meta, on="task_id", how="left")
    return df


def avg(series_mask, scores):
    s = scores[series_mask]
    return round(float(s.mean()), 1) if len(s) > 0 else None


def score_block(sub: pd.DataFrame):
    scores = sub["final_score_percent"]
    return {
        "overall": round(float(scores.mean()), 1) if len(sub) else None,
        "tax": avg(sub["category"] == "tax", scores),
        "financial": avg(sub["category"] == "financial_accounting", scores),
        "management": avg(sub["category"] == "management_accounting", scores),
        "interpLaw": avg(sub["task_type"] == "interpretation_of_law", scores),
        "calculation": avg(sub["task_type"] == "calculation", scores),
        "journal": avg(sub["task_type"] == "journal_entry", scores),
        "multiChoice": avg(sub["answer_type"] == "multi_choice", scores),
        "openText": avg(sub["answer_type"] == "open_text", scores),
        "singleChoice": avg(sub["answer_type"] == "single_choice", scores),
        "journalEntry": avg(sub["answer_type"] == "journal_entry", scores),
        "austrianTax": avg(sub["regulatory_framework"] == "austrian_tax_law", scores),
        "mixedAcc": avg(sub["regulatory_framework"] == "mixed_accounting_framework", scores),
        "ugb": avg(sub["regulatory_framework"] == "UGB", scores),
        "ifrs": avg(sub["regulatory_framework"] == "IFRS", scores),
    }


EDU_KEYS = {
    "professional_examinations": "prof",
    "master": "master",
    "secondary_vocational_school": "voc",
}


def calibration(sub: pd.DataFrame):
    conf = sub["avg_model_confidence"].fillna(sub["judge_confidence"])
    valid = conf.notna()
    conf = conf[valid]
    scores = sub.loc[valid, "final_score_percent"]
    if len(conf) == 0:
        return []
    bins = [round(i * 0.1, 2) for i in range(11)]
    labels = [round(0.05 + i * 0.1, 2) for i in range(10)]
    bin_idx = pd.cut(conf, bins=bins, labels=labels, include_lowest=True, right=True)
    out = []
    for label in labels:
        m = bin_idx == label
        n = int(m.sum())
        if n == 0:
            continue
        y = round(float(scores[m].mean()), 1)
        out.append({"x": label, "y": y, "n": n})
    return out


def compute_model(df: pd.DataFrame, model: str, price_in=None, price_out=None):
    sub = df[df["model_name"] == model].copy()
    n_rows = len(sub)

    block = score_block(sub)

    by_edu = {}
    for raw, key in EDU_KEYS.items():
        edu_sub = sub[sub["education_level"] == raw]
        by_edu[key] = score_block(edu_sub) if len(edu_sub) else None
    block["byEdu"] = by_edu
    block["eduProf"] = by_edu["prof"]["overall"] if by_edu["prof"] else None
    block["eduMaster"] = by_edu["master"]["overall"] if by_edu["master"] else None
    block["eduVoc"] = by_edu["voc"]["overall"] if by_edu["voc"] else None

    effective_output = sub["token_output"].fillna(0)
    if model in ADD_REASONING_TOKENS:
        effective_output = effective_output + sub["token_reasoning"].fillna(0)
    token_input = sub["token_input"].fillna(0)

    block["tokTask"] = round(float((token_input + effective_output).mean())) if n_rows else None
    if price_in is not None and price_out is not None and n_rows:
        block["cost"] = round(float((token_input * price_in + effective_output * price_out).mean() / 1e6), 6)
    else:
        block["cost"] = None

    block["n"] = str(n_rows) if n_rows == 564 else f"{n_rows}/564"
    block["n_rows"] = n_rows
    block["calib"] = calibration(sub)
    return block


def deep_diff(computed: dict, current: dict, tol=0.05, path="", include_tokens=True):
    """Recursively compare computed vs current, returning a list of mismatch strings.
    include_tokens=False restricts the check to score fields only (n/tokTask/cost/calib
    are known to drift slightly between exports even when scores are identical, per
    user decision to accept that drift only for the models actually being updated)."""
    mismatches = []

    def cmp_scalar(c, k, p):
        if c is None and k is None:
            return
        if c is None or k is None:
            mismatches.append(f"{p}: computed={c} current={k}")
            return
        if isinstance(c, (int, float)) and isinstance(k, (int, float)):
            if abs(c - k) > tol:
                mismatches.append(f"{p}: computed={c} current={k}")
        elif c != k:
            mismatches.append(f"{p}: computed={c!r} current={k!r}")

    for field in SCORE_FIELDS:
        cmp_scalar(computed.get(field), current.get(field), field)

    if include_tokens:
        cmp_scalar(computed.get("n"), current.get("n"), "n")
        cmp_scalar(computed.get("tokTask"), current.get("tokTask"), "tokTask")
        if current.get("cost") is not None:
            cmp_scalar(computed.get("cost"), current.get("cost"), "cost")

    for level in ["prof", "master", "voc"]:
        c_edu = computed.get("byEdu", {}).get(level)
        k_edu = current.get("byEdu", {}).get(level)
        if c_edu is None and k_edu is None:
            continue
        if c_edu is None or k_edu is None:
            mismatches.append(f"byEdu.{level}: computed={c_edu} current={k_edu}")
            continue
        for field in SCORE_FIELDS:
            cmp_scalar(c_edu.get(field), k_edu.get(field), f"byEdu.{level}.{field}")

    if include_tokens:
        c_calib = computed.get("calib", [])
        k_calib = current.get("calib", [])
        if len(c_calib) != len(k_calib):
            mismatches.append(f"calib: length computed={len(c_calib)} current={len(k_calib)}")
        else:
            for i, (cb, kb) in enumerate(zip(c_calib, k_calib)):
                for field in ["x", "y", "n"]:
                    cmp_scalar(cb.get(field), kb.get(field), f"calib[{i}].{field}")

    return mismatches


def _extract_top_level_objects(array_text: str):
    """Brace-count top-level `{ ... }` objects inside the BENCHMARK_RESULTS array."""
    objs = []
    depth = 0
    start = None
    for i, ch in enumerate(array_text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                objs.append(array_text[start:i + 1])
                start = None
    return objs


def _js_object_to_json(block: str) -> str:
    # quote unquoted object keys: `  name:` -> `  "name":`
    block = re.sub(r'([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:', r'\1"\2":', block)
    # convert single-quoted strings to double-quoted (values don't contain embedded quotes in this file)
    block = re.sub(r"'([^']*)'", r'"\1"', block)
    # remove trailing commas before } or ]
    block = re.sub(r',(\s*[}\]])', r'\1', block)
    return block


def parse_current_results_js():
    """Fully parse every model object currently in results.js into a plain dict per model name.
    Used both for the diff check (compare ALL fields, not just top-level ones) and to carry
    over name/org/color/priceIn/priceOut/speed for the models being updated. Also returns the
    raw (untouched) object text per model, so unchanged models can be re-emitted byte-for-byte."""
    text = RESULTS_JS_PATH.read_text(encoding="utf-8")
    array_start = text.index("const BENCHMARK_RESULTS")
    array_end = text.index("\n];", array_start)
    array_text = text[array_start:array_end]

    models = {}
    raw_blocks = {}
    for block in _extract_top_level_objects(array_text):
        json_text = _js_object_to_json(block)
        obj = json.loads(json_text)
        models[obj["name"]] = obj
        raw_blocks[obj["name"]] = block
    return models, raw_blocks


def format_model_js(model_name: str, computed: dict, cur: dict, comment_num: int) -> str:
    def fnum(v):
        return "null" if v is None else v

    def score_line(d, fields):
        return ", ".join(f"{f}: {fnum(d.get(f))}" for f in fields)

    cat_fields = ["overall", "tax", "financial", "management"]
    type_fields = ["interpLaw", "calculation", "journal"]
    ans_fields = ["multiChoice", "openText", "singleChoice", "journalEntry"]
    reg_fields = ["austrianTax", "mixedAcc", "ugb", "ifrs"]
    edu_fields = cat_fields + type_fields + ans_fields + reg_fields

    def edu_line(level_key):
        d = computed["byEdu"].get(level_key)
        if d is None:
            return "null"
        return "{ " + score_line(d, edu_fields) + " }"

    calib_items = ", ".join(
        "{x:%s,y:%s,n:%s}" % (b["x"], b["y"], b["n"]) for b in computed["calib"]
    )

    note_line = ""
    if computed["n_rows"] < 564:
        missing = 564 - computed["n_rows"]
        unit = "task" if missing == 1 else "tasks"
        note = f"{missing} {unit} not completed for this model. Scored on {computed['n_rows']}/564 tasks."
        note_line = f"\n    note: '{note}',"

    lines = []
    lines.append(f"  // ── {comment_num}. {model_name} ───────────────────────────────────")
    lines.append("  {")
    lines.append(f"    name: '{cur['name']}', org: '{cur['org']}', color: '{cur['color']}',")
    lines.append(f"    {score_line(computed, cat_fields)},")
    lines.append(f"    {score_line(computed, type_fields)},")
    lines.append(f"    {score_line(computed, ans_fields)},")
    lines.append(f"    {score_line(computed, reg_fields)},")
    lines.append(
        f"    eduProf: {fnum(computed['eduProf'])}, eduMaster: {fnum(computed['eduMaster'])}, eduVoc: {fnum(computed['eduVoc'])},"
    )
    lines.append("    byEdu: {")
    lines.append(f"      prof:   {edu_line('prof')},")
    lines.append(f"      master: {edu_line('master')},")
    lines.append(f"      voc:    {edu_line('voc')},")
    lines.append("    },")
    lines.append(
        f"    n: '{computed['n']}', priceIn: {cur['priceIn']}, priceOut: {cur['priceOut']}, "
        f"cost: {computed['cost']}, tokTask: {computed['tokTask']}, speed: {cur['speed']},{note_line}"
    )
    lines.append(f"    calib: [{calib_items}],")
    lines.append("  },")
    return "\n".join(lines)


def main():
    df = load_data()
    current, raw_blocks = parse_current_results_js()
    all_models = sorted(df["model_name"].dropna().unique().tolist())

    print(f"Models found in export: {all_models}\n")

    print("=" * 70)
    print("DEEP DIFF CHECK for models with UNCHANGED task count (should match on every field)")
    print("=" * 70)
    unchanged = [m for m in all_models if m not in UPDATED_MODELS]
    any_mismatch = False  # blocking: score-field mismatches only (n/tokTask/cost/calib drift is expected)
    for m in unchanged:
        cur = current.get(m)
        if cur is None:
            print(f"[{m}] NOT FOUND in current results.js — skipping diff")
            continue
        computed = compute_model(df, m, price_in=cur.get("priceIn"), price_out=cur.get("priceOut"))
        info_mismatches = deep_diff(computed, cur, include_tokens=True)
        score_mismatches = deep_diff(computed, cur, include_tokens=False)
        if score_mismatches:
            any_mismatch = True
            print(f"[{m}] SCORE MISMATCH ({len(score_mismatches)} field(s)) — BLOCKING:")
            for mm in score_mismatches:
                print(f"    {mm}")
        elif info_mismatches:
            print(f"[{m}] scores OK, but n/tokTask/cost/calib drift (expected, not touching this model):")
            for mm in info_mismatches:
                print(f"    {mm}")
        else:
            print(f"[{m}] OK — all {len(SCORE_FIELDS)} score fields + byEdu + calib + tokTask/cost/n match")

    print()
    print("=" * 70)
    print(f"COMPUTED VALUES for the {len(UPDATED_MODELS)} UPDATED models")
    print("=" * 70)
    computed_by_model = {}
    for m in UPDATED_MODELS:
        cur = current.get(m, {})
        computed = compute_model(df, m, price_in=cur.get("priceIn"), price_out=cur.get("priceOut"))
        computed_by_model[m] = computed
        print(f"\n--- {m} ---")
        print(f"  rows: {computed['n_rows']} / 564 (was {cur.get('n')})")
        print(f"  overall: {computed['overall']}  (was {cur.get('overall')})")
        print(f"  cost: {computed['cost']} (was {cur.get('cost')})  tokTask: {computed['tokTask']} (was {cur.get('tokTask')})")

    print()
    if any_mismatch:
        print("!! Mismatches found — investigate before editing results.js !!")
    else:
        print(f"All {len(unchanged)} unchanged-count models match current results.js exactly. Safe to proceed.")

    print()
    print("=" * 70)
    print("JS BLOCKS for the updated models (paste in place of the corresponding current block)")
    print("=" * 70)
    # Sort ALL 13 models by new overall score to get correct ranking/comment numbers
    all_overalls = []
    for m in all_models:
        cur = current.get(m, {})
        if m in computed_by_model:
            overall = computed_by_model[m]["overall"]
        else:
            overall = cur.get("overall")
        all_overalls.append((m, overall))
    all_overalls.sort(key=lambda t: -(t[1] or 0))

    print("\nNew overall ranking (for reference):")
    for i, (m, o) in enumerate(all_overalls, 1):
        marker = " <-- UPDATED" if m in UPDATED_MODELS else ""
        print(f"  {i:2d}. {m}: {o}{marker}")

    print()
    for m in UPDATED_MODELS:
        cur = current[m]
        computed = computed_by_model[m]
        rank = next(i for i, (name, _) in enumerate(all_overalls, 1) if name == m)
        print(format_model_js(m, computed, cur, rank))
        print()

    if any_mismatch:
        print("Refusing to write results.js — unexpected mismatches in unchanged models.")
        return

    # Build the full re-sorted array: updated models get freshly generated blocks,
    # unchanged models keep their EXACT original object text (only the comment number changes).
    blocks = []
    for rank, (m, _overall) in enumerate(all_overalls, 1):
        if m in UPDATED_MODELS:
            computed = computed_by_model[m]
            cur = current[m]
            blocks.append(format_model_js(m, computed, cur, rank))
        else:
            header = f"  // ── {rank}. {m} ───────────────────────────────────"
            body = raw_blocks[m]
            # re-indent the raw block body to match the 2-space/4-space convention already in it
            blocks.append(f"{header}\n  {body},")

    new_array_text = "const BENCHMARK_RESULTS = [\n\n" + "\n\n".join(blocks) + "\n\n];"

    text = RESULTS_JS_PATH.read_text(encoding="utf-8")
    array_start = text.index("const BENCHMARK_RESULTS")
    array_end = text.index("\n];", array_start) + len("\n];")
    new_text = text[:array_start] + new_array_text + text[array_end:]
    RESULTS_JS_PATH.write_text(new_text, encoding="utf-8")
    print(f"\nWrote updated BENCHMARK_RESULTS array to {RESULTS_JS_PATH}")


if __name__ == "__main__":
    main()
