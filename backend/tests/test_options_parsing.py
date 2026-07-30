"""
Options parsing (backend/batch_run.py) and the dry-run data-quality gate
(backend/batch_utils.py check_field_consistency).

The gate exists because none of these defects are visible in a score:
score_sc_mc_percent() never validates answer letters against the task's
options, so a swallowed option or a gold citing a non-existent letter produces
plausible-looking numbers on a broken task. These tests pin the detection.
"""

import pytest

from backend.batch_run import parse_options
from backend.batch_utils import check_field_consistency


def _task(**overrides):
    """A minimal valid multi_choice task dict; override to introduce a defect."""
    task = {
        "question_id": "t_0001",
        "answer_type": "multi_choice",
        "grading_criteria": "",
        "numeric_tolerance": None,
        "options": {"A": "first", "B": "second", "C": "third"},
        "gold_answer": "A,C",
    }
    task.update(overrides)
    return task


# ─────────────────────────────────────────────────────────────────────────────
# parse_options — the supported source formats
# ─────────────────────────────────────────────────────────────────────────────

def test_parses_letter_prefix_per_line():
    assert parse_options("A) Innerbetriebliche Abrechnung\nB) Ausserbetriebliche Abrechnung") == {
        "A": "Innerbetriebliche Abrechnung",
        "B": "Ausserbetriebliche Abrechnung",
    }


def test_parses_pipe_separated():
    assert parse_options("A) first | B) second | C) third") == {
        "A": "first", "B": "second", "C": "third",
    }


def test_parses_parenthesis_prefixed():
    got = parse_options("(A) first | (B) second")
    assert got == {"A": "first", "B": "second"}


def test_parses_json_passthrough():
    assert parse_options('{"A": "first", "B": "second"}') == {"A": "first", "B": "second"}


def test_uppercases_lowercase_keys():
    """Sheets sometimes use a) b) — pipeline uppercases valid_choices, so the
    stored keys must be uppercase too or every answer is filtered out."""
    assert parse_options("a) first\nb) second") == {"A": "first", "B": "second"}


@pytest.mark.parametrize("raw", [None, "", "   "])
def test_blank_options_are_none(raw):
    assert parse_options(raw) is None


def test_unrecognised_format_falls_back_to_raw():
    """The {"raw": ...} fallback is what makes valid_choices become ["RAW"],
    filtering out every model answer and scoring the whole task 0. The dry-run
    OPTS check exists to catch it before a run."""
    got = parse_options("- first bullet\n- second bullet")
    assert list(got.keys()) == ["raw"]


def test_two_options_on_one_line_swallows_the_second():
    """Documents the root cause of task 12015528_0041 being unwinnable.

    parse_options only treats "X)" as a new option at the start of a line, so a
    mid-line "C)" is absorbed into B's text and C vanishes from the keys. Not
    "fixed" by loosening the regex: German legal citations ("Z 2 lit b) EStG")
    would then split wrongly across the whole corpus. Detected instead.
    """
    got = parse_options("A) first\nB) second C) third")
    assert set(got.keys()) == {"A", "B"}
    assert "C)" in got["B"]


# ─────────────────────────────────────────────────────────────────────────────
# check_field_consistency — warning codes
# ─────────────────────────────────────────────────────────────────────────────

def test_clean_task_produces_no_warnings():
    assert check_field_consistency([_task()]) == 0


def test_type_flags_unrecognised_answer_type():
    """A blank trailing row in a sheet imports as a live, public, unscoreable
    task — exactly how the empty '_0000' task reached the leaderboard."""
    assert check_field_consistency([_task(answer_type="")]) >= 1


def test_miss_flags_open_text_without_rubric():
    assert check_field_consistency([
        _task(answer_type="open_text", options=None, gold_answer="freitext", grading_criteria="")
    ]) >= 1


def test_miss_flags_open_numeric_without_tolerance():
    assert check_field_consistency([
        _task(answer_type="open_numeric", options=None, gold_answer="42",
              grading_criteria="rubric", numeric_tolerance=None)
    ]) >= 1


def test_tol_flags_unparseable_tolerance():
    """A populated-but-unparseable tolerance is worse than a blank one: the
    sheet looks correct while the judge silently receives no tolerance band."""
    assert check_field_consistency([
        _task(answer_type="open_numeric", options=None, gold_answer="42",
              grading_criteria="rubric", numeric_tolerance="ca. eins")
    ]) >= 1


def test_parseable_annotated_tolerance_is_accepted():
    assert check_field_consistency([
        _task(answer_type="open_numeric", options=None, gold_answer="42",
              grading_criteria="rubric", numeric_tolerance="+/- 1")
    ]) == 0


def test_opts_flags_raw_options():
    assert check_field_consistency([
        _task(options={"raw": "- first\n- second"}, gold_answer="A")
    ]) >= 1


def test_opts_flags_buried_option_marker():
    assert check_field_consistency([
        _task(options={"A": "first", "B": "second C) third", "D": "fourth"},
              gold_answer="A,B")
    ]) >= 1


def test_opts_flags_gap_in_option_letters():
    assert check_field_consistency([
        _task(options={"A": "first", "B": "second", "D": "fourth"}, gold_answer="A,B")
    ]) >= 1


def test_gold_flags_letter_with_no_matching_option():
    """The task 12015528_0041 signature: gold cites C, options are A/B/D/E, so
    no model can ever score full marks."""
    assert check_field_consistency([
        _task(options={"A": "a", "B": "b", "D": "d", "E": "e"}, gold_answer="C,D")
    ]) >= 1


def test_gold_flags_semicolon_delimiter():
    """gold_set() splits on ',' only, so a ';' gold is one bogus token and
    every model scores 0."""
    assert check_field_consistency([_task(gold_answer="A;C")]) >= 1


def test_warning_codes_are_emitted_for_the_unwinnable_task(caplog):
    """Assert the operator-facing codes, not just the count."""
    import logging
    with caplog.at_level(logging.WARNING, logger="batch_utils"):
        check_field_consistency([
            _task(options={"A": "a", "B": "b", "D": "d", "E": "e"}, gold_answer="C,D")
        ])
    text = caplog.text
    assert "OPTS" in text   # letter gap: A, B, D, E is missing C
    assert "GOLD" in text   # gold cites C, which has no option


def test_open_types_are_not_subjected_to_choice_checks():
    """Option/gold integrity rules must not fire on open-ended tasks."""
    assert check_field_consistency([
        _task(answer_type="open_text", options=None,
              gold_answer="Ein Ertrag iHv 60 T EUR; plus Anhangangabe",
              grading_criteria="rubric")
    ]) == 0
