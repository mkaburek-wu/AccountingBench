"""
results.js export helpers (backend/recompute_results.py).

These are the functions that turn benchmark rows into the BENCHMARK_RESULTS
block the public site reads, and that decide whether a model's numbers changed.
A silent defect here mis-publishes scores, so the parsing/diffing edges are
pinned here — especially the results.js round-trip, which uses regex-based
JS-to-JSON conversion.
"""

import pandas as pd
import pytest

from backend.recompute_results import (
    _extract_top_level_objects,
    _js_object_to_json,
    avg,
    calibration,
    deep_diff,
    score_block,
)


def _rows(records):
    return pd.DataFrame.from_records(records)


def _row(score, *, category="tax", task_type="calculation",
         answer_type="multi_choice", framework="IFRS",
         edu="professional_examinations", conf=None, judge_conf=None):
    return {
        "final_score_percent": score,
        "category": category,
        "task_type": task_type,
        "answer_type": answer_type,
        "regulatory_framework": framework,
        "education_level": edu,
        "avg_model_confidence": conf,
        "judge_confidence": judge_conf,
    }


# ─────────────────────────────────────────────────────────────────────────────
# avg / score_block
# ─────────────────────────────────────────────────────────────────────────────

def test_avg_rounds_to_one_decimal():
    df = _rows([_row(100.0), _row(0.0), _row(50.0)])
    assert avg(df["category"] == "tax", df["final_score_percent"]) == 50.0


def test_avg_of_empty_selection_is_none():
    """A model with no rows in a category must publish null, not 0 — a 0 would
    read as "scored badly" instead of "not measured"."""
    df = _rows([_row(100.0, category="tax")])
    assert avg(df["category"] == "management_accounting", df["final_score_percent"]) is None


def test_score_block_partitions_by_every_dimension():
    df = _rows([
        _row(100.0, category="tax", task_type="calculation",
             answer_type="multi_choice", framework="IFRS"),
        _row(0.0, category="financial_accounting", task_type="interpretation_of_law",
             answer_type="open_text", framework="austrian_tax_law"),
    ])
    block = score_block(df)
    assert block["overall"] == 50.0
    assert block["tax"] == 100.0
    assert block["financial"] == 0.0
    assert block["management"] is None
    assert block["calculation"] == 100.0
    assert block["interpLaw"] == 0.0
    assert block["multiChoice"] == 100.0
    assert block["openText"] == 0.0
    assert block["ifrs"] == 100.0
    assert block["austrianTax"] == 0.0


# ─────────────────────────────────────────────────────────────────────────────
# calibration
# ─────────────────────────────────────────────────────────────────────────────

def test_calibration_bins_by_confidence_decile():
    df = _rows([
        _row(100.0, conf=0.95), _row(80.0, conf=0.92),   # -> 0.95 bin
        _row(0.0, conf=0.15),                            # -> 0.15 bin
    ])
    out = calibration(df)
    by_x = {b["x"]: b for b in out}
    assert by_x[0.95]["n"] == 2
    assert by_x[0.95]["y"] == 90.0
    assert by_x[0.15]["n"] == 1
    assert by_x[0.15]["y"] == 0.0


def test_calibration_falls_back_to_judge_confidence():
    """Some providers report no model confidence; the judge's own confidence is
    used so those rows still appear on the calibration chart."""
    df = _rows([_row(100.0, conf=None, judge_conf=0.85)])
    assert calibration(df) == [{"x": 0.85, "y": 100.0, "n": 1}]


def test_calibration_without_any_confidence_is_empty():
    df = _rows([_row(100.0, conf=None, judge_conf=None)])
    assert calibration(df) == []


def test_calibration_omits_empty_bins():
    df = _rows([_row(50.0, conf=0.55)])
    assert len(calibration(df)) == 1


def test_calibration_is_stable_against_float_noise_at_bin_edges():
    """Confidences are means of three trials, so many land exactly on a decile
    edge — and float noise decided which side. The same value reads as
    0.20000000000000004 from SQLite but 0.2 from an Excel round-trip, which
    silently moved rows between calibration bins. Binning must not depend on
    that representation.
    """
    noisy = calibration(_rows([_row(40.0, conf=0.20000000000000004)]))
    clean = calibration(_rows([_row(40.0, conf=0.2)]))
    assert noisy == clean


# ─────────────────────────────────────────────────────────────────────────────
# deep_diff
# ─────────────────────────────────────────────────────────────────────────────

def test_deep_diff_clean_when_identical():
    block = {"overall": 80.0, "byEdu": {}, "calib": [], "n": "564"}
    assert deep_diff(block, dict(block), include_tokens=False) == []


def test_deep_diff_tolerates_sub_threshold_float_drift():
    """Rounding noise between exports must not be reported as a score change."""
    a = {"overall": 80.00, "byEdu": {}, "calib": []}
    b = {"overall": 80.04, "byEdu": {}, "calib": []}
    assert deep_diff(a, b, include_tokens=False) == []


def test_deep_diff_reports_a_real_score_change():
    a = {"overall": 80.0, "byEdu": {}, "calib": []}
    b = {"overall": 75.0, "byEdu": {}, "calib": []}
    assert len(deep_diff(a, b, include_tokens=False)) == 1


def test_deep_diff_reports_none_vs_value_asymmetry():
    """None -> number means a dimension became measured (or stopped being);
    that must never be silently ignored."""
    a = {"overall": 80.0, "management": None, "byEdu": {}, "calib": []}
    b = {"overall": 80.0, "management": 40.0, "byEdu": {}, "calib": []}
    assert len(deep_diff(a, b, include_tokens=False)) == 1


def test_deep_diff_compares_byedu_breakdowns():
    a = {"byEdu": {"prof": {"overall": 90.0}}, "calib": []}
    b = {"byEdu": {"prof": {"overall": 70.0}}, "calib": []}
    assert any("byEdu.prof" in m for m in deep_diff(a, b, include_tokens=False))


def test_include_tokens_toggles_n_and_cost_comparison():
    a = {"byEdu": {}, "calib": [], "n": "564", "tokTask": 100, "cost": 0.001}
    b = {"byEdu": {}, "calib": [], "n": "563/564", "tokTask": 999, "cost": 0.002}
    assert deep_diff(a, b, include_tokens=False) == []
    assert deep_diff(a, b, include_tokens=True) != []


# ─────────────────────────────────────────────────────────────────────────────
# results.js round-trip
# ─────────────────────────────────────────────────────────────────────────────

def test_extract_top_level_objects_handles_nested_braces():
    """byEdu nests objects, so a naive split on '}' would truncate a model."""
    text = "[ { name: 'A', byEdu: { prof: { overall: 1 } } }, { name: 'B' } ]"
    objs = _extract_top_level_objects(text)
    assert len(objs) == 2
    assert "byEdu" in objs[0]
    assert "'B'" in objs[1]


def test_js_object_to_json_round_trips_a_model_block():
    import json
    block = "{ name: 'gpt-5.5', overall: 80.3, byEdu: { prof: null }, calib: [{x:0.95,y:90,n:5}], }"
    obj = json.loads(_js_object_to_json(block))
    assert obj["name"] == "gpt-5.5"
    assert obj["overall"] == 80.3
    assert obj["byEdu"]["prof"] is None
    assert obj["calib"] == [{"x": 0.95, "y": 90, "n": 5}]


@pytest.mark.xfail(reason=(
    "Known fragility: the single->double quote conversion is a bare regex, so "
    "an apostrophe inside any single-quoted JS string (a hand-written note, or "
    "an org like \"O'Reilly\") corrupts the JSON. Safe today only because note "
    "text is machine-generated. Should escape or raise instead of mis-parsing."
), strict=True)
def test_js_object_to_json_survives_an_apostrophe_in_a_string():
    import json
    block = "{ name: 'A', org: 'O'Reilly', overall: 80.0 }"
    obj = json.loads(_js_object_to_json(block))
    assert obj["org"] == "O'Reilly"
