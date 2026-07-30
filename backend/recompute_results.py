"""
Regenerate public/results.js from benchmark results.

Computes every BENCHMARK_RESULTS field per model (category / task-type /
answer-type / framework / education-level scores, byEdu breakdown, calibration
bins, tokens and cost), diffs the result against what results.js currently
says, and — with --write — rewrites the BENCHMARK_RESULTS array in place.

The database is the source of truth: `public/results.js` is a generated
artefact, so nothing here should ever be edited by hand.

Usage (from project root):
    # report only — computes, diffs, writes nothing. Exits 1 on a score change.
    python -m backend.recompute_results --check

    # regenerate results.js (refuses to write if an unexpected score moved)
    python -m backend.recompute_results --write

    # restrict the "expected to change" set; every other model is diff-checked
    # strictly and must match results.js exactly
    python -m backend.recompute_results --write --models "gpt-5.5,Kimi-K2.6"

    # reproduce an older run from an Excel export instead of the live DB
    python -m backend.recompute_results --check --from-excel backend/uploads/300726_results_N564.xlsx

Models named by --models are treated as "expected to change" and are written
with freshly computed values. Every other model is compared field-by-field
against results.js; any score difference is treated as unexpected and blocks a
--write. With no --models, every model in the data is refreshed.
"""
import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RESULTS_JS_PATH = ROOT / "public" / "results.js"

# Task-metadata columns the score partitioning needs, in both data sources.
TASK_COLUMNS = [
    "id", "category", "task_type", "answer_type",
    "regulatory_framework", "education_level",
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


def _merge(tasks: pd.DataFrame, outputs: pd.DataFrame) -> pd.DataFrame:
    """Attach task metadata to each output row (shared by both data sources)."""
    task_meta = tasks[TASK_COLUMNS].rename(columns={"id": "task_id"})
    return outputs.merge(task_meta, on="task_id", how="left")


def load_data_from_db(public_only: bool = True) -> pd.DataFrame:
    """Read benchmark rows straight from the database — the default source.

    Reading the DB rather than a dated Excel export removes the manual
    export step, and with it the risk of publishing numbers computed from a
    snapshot that predates the latest repair or re-run.

    Only public tasks are counted by default, matching what the site reports.
    """
    from backend.database import SessionLocal
    from backend.models import BenchmarkOutput, BenchmarkTask

    db = SessionLocal()
    try:
        task_q = db.query(*[getattr(BenchmarkTask, c) for c in TASK_COLUMNS])
        if public_only:
            task_q = task_q.filter(BenchmarkTask.is_public.is_(True))
        tasks = pd.DataFrame(task_q.all(), columns=TASK_COLUMNS)

        out_cols = [
            "task_id", "model_name", "final_score_percent",
            "avg_model_confidence", "judge_confidence",
            "token_input", "token_output", "token_reasoning",
        ]
        outputs = pd.DataFrame(
            db.query(*[getattr(BenchmarkOutput, c) for c in out_cols]).all(),
            columns=out_cols,
        )
    finally:
        db.close()

    # Inner-join semantics: outputs belonging to non-public tasks are dropped.
    df = _merge(tasks, outputs)
    return df[df["category"].notna()].copy() if public_only else df


def load_data_from_excel(xlsx_path: Path) -> pd.DataFrame:
    """Read from a DB→Excel export. Kept so an earlier published run can be
    reproduced exactly, and as an independent cross-check of the DB path."""
    tasks = pd.read_excel(xlsx_path, sheet_name="benchmark_tasks")
    outputs = pd.read_excel(xlsx_path, sheet_name="benchmark_outputs")
    return _merge(tasks, outputs)


def count_tasks(df: pd.DataFrame) -> int:
    """Total distinct tasks in the dataset — the denominator for `n`/`note`.

    Derived, never hardcoded: the count changes whenever tasks are added or
    removed, and a stale literal silently mislabels every model's coverage.
    """
    return int(df["task_id"].nunique())


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
    # Round before binning. Confidences are means of three trial values, so many
    # land exactly on a decile edge — and float noise decides which side. The
    # same value reads as 0.20000000000000004 from SQLite but 0.2 from an Excel
    # round-trip, putting it in a different bin and shifting calib counts for
    # otherwise identical data. Rounding makes the bins reproducible.
    conf = conf.round(6)
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


def compute_model(df: pd.DataFrame, model: str, price_in=None, price_out=None,
                  total_tasks: int | None = None):
    sub = df[df["model_name"] == model].copy()
    n_rows = len(sub)
    if total_tasks is None:
        total_tasks = count_tasks(df)

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

    block["n"] = str(n_rows) if n_rows == total_tasks else f"{n_rows}/{total_tasks}"
    block["n_rows"] = n_rows
    block["total_tasks"] = total_tasks
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
    """Convert one JS model object literal into strict JSON.

    Single-quoted JS strings are rewritten to double-quoted JSON strings by
    regex, which cannot represent an apostrophe *inside* such a string. Rather
    than silently emitting mangled JSON (an `org` of "O'Reilly", or a
    hand-edited `note`, would corrupt the whole object and hence the diff), an
    odd number of quotes is rejected outright.
    """
    if block.count("'") % 2 != 0:
        raise ValueError(
            "Cannot parse results.js: an odd number of single quotes in a model "
            "object suggests an apostrophe inside a string value, which this "
            "converter cannot represent. Use a double-quoted string, or escape "
            "the apostrophe, in:\n" + block[:200]
        )
    # quote unquoted object keys: `  name:` -> `  "name":`
    block = re.sub(r'([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:', r'\1"\2":', block)
    # convert single-quoted strings to double-quoted
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

    total = computed.get("total_tasks")
    note_line = ""
    if total and computed["n_rows"] < total:
        missing = total - computed["n_rows"]
        unit = "task" if missing == 1 else "tasks"
        note = (f"{missing} {unit} not completed for this model. "
                f"Scored on {computed['n_rows']}/{total} tasks.")
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


def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Regenerate public/results.js from benchmark results.",
    )
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true",
                     help="Compute and diff only; write nothing. Exits 1 on an "
                          "unexpected score change. This is the default.")
    mode.add_argument("--write", action="store_true",
                     help="Rewrite the BENCHMARK_RESULTS array in public/results.js "
                          "(refuses if an unexpected score moved).")
    p.add_argument("--models", default=None,
                   help="Comma-separated models expected to change. Every other "
                        "model is diff-checked strictly. Default: all models.")
    p.add_argument("--from-excel", default=None, metavar="PATH",
                   help="Read from a DB→Excel export instead of the live database.")
    p.add_argument("--include-private", action="store_true",
                   help="Include non-public tasks (DB source only). Default: "
                        "public tasks only, matching the site.")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    if args.from_excel:
        df = load_data_from_excel(Path(args.from_excel))
        source = f"Excel export {args.from_excel}"
    else:
        df = load_data_from_db(public_only=not args.include_private)
        source = "database" + ("" if args.include_private else " (public tasks only)")

    total_tasks = count_tasks(df)
    current, raw_blocks = parse_current_results_js()
    all_models = sorted(df["model_name"].dropna().unique().tolist())

    # results.js is the publication surface: name/org/color/priceIn/priceOut/
    # speed are curated by hand and cannot be derived from the DB. A model with
    # no entry there is deliberately unpublished (e.g. partial coverage), not an
    # error — so it is reported and skipped rather than blocking the run.
    published   = [m for m in all_models if m in current]
    unpublished = [m for m in all_models if m not in current]

    # Models named by --models are "expected to change"; everything else must
    # match results.js exactly. With no --models, refresh every published model.
    if args.models:
        updated_models = [m.strip() for m in args.models.split(",") if m.strip()]
        unknown = [m for m in updated_models if m not in all_models]
        if unknown:
            print(f"!! --models names models absent from the data: {unknown}")
            return 1
    else:
        updated_models = list(published)

    print(f"Source: {source}")
    print(f"Tasks:  {total_tasks}")
    print(f"Models: {len(published)} published, {len(all_models)} in data")
    if unpublished:
        print(f"        not in results.js, skipped: {unpublished}")
    print()

    print("=" * 70)
    print("DEEP DIFF CHECK for models NOT expected to change (must match on every field)")
    print("=" * 70)
    unchanged = [m for m in published if m not in updated_models]
    if not unchanged:
        print("  (none — every model is being refreshed)")
    any_mismatch = False  # blocking: score-field mismatches only (n/tokTask/cost/calib drift is expected)
    for m in unchanged:
        cur = current.get(m)
        if cur is None:
            print(f"[{m}] NOT FOUND in current results.js — skipping diff")
            continue
        computed = compute_model(df, m, price_in=cur.get("priceIn"),
                                 price_out=cur.get("priceOut"), total_tasks=total_tasks)
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
    print(f"COMPUTED VALUES for the {len(updated_models)} model(s) being refreshed")
    print("=" * 70)
    computed_by_model = {}
    for m in updated_models:
        cur = current.get(m, {})
        computed = compute_model(df, m, price_in=cur.get("priceIn"),
                                 price_out=cur.get("priceOut"), total_tasks=total_tasks)
        computed_by_model[m] = computed
        print(f"\n--- {m} ---")
        print(f"  rows: {computed['n_rows']} / {total_tasks} (was {cur.get('n')})")
        print(f"  overall: {computed['overall']}  (was {cur.get('overall')})")
        print(f"  cost: {computed['cost']} (was {cur.get('cost')})  tokTask: {computed['tokTask']} (was {cur.get('tokTask')})")

    print()
    if any_mismatch:
        print("!! Mismatches found — investigate before editing results.js !!")
    elif unchanged:
        print(f"All {len(unchanged)} model(s) not expected to change match results.js exactly.")

    # Rank the published models by new overall score for the comment numbering.
    all_overalls = []
    for m in published:
        cur = current.get(m, {})
        overall = computed_by_model[m]["overall"] if m in computed_by_model else cur.get("overall")
        all_overalls.append((m, overall))
    all_overalls.sort(key=lambda t: -(t[1] or 0))

    print()
    print("=" * 70)
    print("NEW OVERALL RANKING")
    print("=" * 70)
    for i, (m, o) in enumerate(all_overalls, 1):
        was = current.get(m, {}).get("overall")
        moved = "" if was is None or o is None or abs(o - was) <= 0.05 else f"  (was {was})"
        print(f"  {i:2d}. {m}: {o}{moved}")

    if any_mismatch:
        print("\nRefusing to write: unexpected score changes in models not listed in --models.")
        print("Re-run with those models included in --models if the change is intended.")
        return 1

    missing_meta = [m for m in updated_models if m not in current]
    if missing_meta:
        # name/org/color/priceIn/priceOut/speed are curated by hand and cannot
        # be derived from the DB, so a brand-new model needs a stub block first.
        print(f"\n!! No existing results.js entry for: {missing_meta}")
        print("   Add a block with name/org/color/priceIn/priceOut/speed first; "
              "the score fields will then be generated.")
        return 1

    if not args.write:
        print("\n--check: no changes written. Re-run with --write to update results.js.")
        return 0

    # Rebuild the array: refreshed models get freshly generated blocks, all
    # others keep their EXACT original object text so the diff stays minimal.
    blocks = []
    for rank, (m, _overall) in enumerate(all_overalls, 1):
        if m in computed_by_model:
            blocks.append(format_model_js(m, computed_by_model[m], current[m], rank))
        else:
            header = f"  // ── {rank}. {m} ───────────────────────────────────"
            blocks.append(f"{header}\n  {raw_blocks[m]},")

    new_array_text = "const BENCHMARK_RESULTS = [\n\n" + "\n\n".join(blocks) + "\n\n];"

    text = RESULTS_JS_PATH.read_text(encoding="utf-8")
    array_start = text.index("const BENCHMARK_RESULTS")
    array_end = text.index("\n];", array_start) + len("\n];")
    new_text = text[:array_start] + new_array_text + text[array_end:]
    RESULTS_JS_PATH.write_text(new_text, encoding="utf-8")
    print(f"\nWrote updated BENCHMARK_RESULTS array to {RESULTS_JS_PATH}")
    print("Review with: git diff public/results.js")
    return 0


if __name__ == "__main__":
    sys.exit(main())
