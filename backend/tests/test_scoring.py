"""
Scoring and answer-parsing tests (backend/processing/pipeline.py).

Most cases here are real regressions found by auditing the live database — the
docstring on each test names the failure it guards against, so a future change
that reintroduces the bug fails loudly instead of silently rescoring the
benchmark.
"""

import pytest

from backend.processing.pipeline import (
    ALL_MODELS,
    MODEL_REGISTRY,
    build_judge_prompt,
    gold_set,
    majority_vote,
    parse_choice_id,
    parse_choice_set,
    parse_number,
    parse_tolerance,
    score_sc_mc_percent,
)

A_E = list("ABCDE")
A_F = list("ABCDEF")


# ─────────────────────────────────────────────────────────────────────────────
# parse_choice_set — compact multi-select answers
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("text,valid,expected", [
    ("BC",   A_E, ["B", "C"]),
    ("AC",   A_E, ["A", "C"]),
    ("CE",   A_E, ["C", "E"]),
    ("BCE",  A_E, ["B", "C", "E"]),
    ("ABCD", A_E, ["A", "B", "C", "D"]),
    ("BEF",  A_F, ["B", "E", "F"]),
])
def test_compact_letter_runs_are_parsed(text, valid, expected):
    """Claude opus models answer multi-select as a separator-less run ("BC").

    The word-boundary regex finds nothing in that case, so before the fallback
    existed these answers were stored empty and scored 0 despite being correct.
    """
    assert parse_choice_set(text, valid=valid) == expected


@pytest.mark.parametrize("text,valid", [
    # German/English words made purely of valid option letters. A loose
    # "all chars are valid letters" rule misreads every one of these.
    ("CAFE",   A_F),
    ("FACADE", A_F),
    ("FADE",   A_F),
    ("DEAF",   A_F),
    ("BAD",    A_E),
    ("CAB",    A_E),
    ("DAB",    A_E),
    ("BEAD",   A_E),
    ("DEAD",   A_E),   # repeated letter
    ("EBBE",   A_E),   # repeated letter
    ("ABBA",   A_E),   # repeated letter
    ("DECADE", A_E),
    ("EDDA",   A_E),
    ("DA",     A_E),   # descending -> not a choice enumeration
    ("Die Antwort ist ab", A_E),   # run buried inside prose
])
def test_prose_is_not_misread_as_a_choice_set(text, valid):
    """The compact-run fallback must not fire on ordinary words.

    Guarded by four rules: whole-answer only, no repeated letters, no more
    letters than options, and ascending order.
    """
    assert parse_choice_set(text, valid=valid) == []


@pytest.mark.parametrize("text,expected", [
    ("B,C",          ["B", "C"]),
    ("A, B und C",   ["A", "B", "C"]),
    ("(A) (C)",      ["A", "C"]),
    ("A",            ["A"]),
    ("",             []),
    ("XY",           []),                       # letters outside `valid`
    ("Alle Aussagen sind falsch.", []),
])
def test_standard_answer_formats_still_work(text, expected):
    """The fallback must not regress the formats that always worked."""
    assert parse_choice_set(text, valid=A_E) == expected


def test_ascending_two_letter_answer_is_accepted_by_design():
    """A bare "AB" to a multi-choice question really does mean A and B.

    Documents an intentional acceptance: it is indistinguishable from the
    German word "ab", but reading it as a choice set is the better default.
    """
    assert parse_choice_set("AB", valid=A_E) == ["A", "B"]


def test_compact_run_longer_than_option_count_is_rejected():
    assert parse_choice_set("ABCDEF", valid=list("ABC")) == []


# ─────────────────────────────────────────────────────────────────────────────
# score_sc_mc_percent
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("answer,gold,expected", [
    ("A,C",   "A,C",   100.0),   # exact match
    ("C",     "A,C",    50.0),   # one of two correct, none wrong
    ("C,E",   "A,C",     0.0),   # one right, one wrong -> nets to 0
    ("A,B,C", "A,B,C", 100.0),
    ("A",     "A,B,C", pytest.approx(33.33, abs=0.01)),
    ("A,B",   "A,B,C", pytest.approx(66.67, abs=0.01)),
    ("A",     "A",     100.0),
    ("B",     "A",       0.0),
    ("",      "A,C",     0.0),   # empty answer never scores
])
def test_sc_mc_formula(answer, gold, expected):
    """unit*correct - unit*incorrect, clamped to [0, 100]."""
    assert score_sc_mc_percent(answer, gold) == expected


def test_score_is_clamped_and_never_negative():
    """Marking every wrong option must floor at 0, not go negative."""
    assert score_sc_mc_percent("B,C,D,E", "A") == 0.0


def test_score_is_case_and_whitespace_insensitive():
    assert score_sc_mc_percent(" a , c ", "A,C") == 100.0


def test_empty_gold_scores_zero():
    assert score_sc_mc_percent("A", "") == 0.0


@pytest.mark.xfail(reason=(
    "Known latent bug: a comma-less multi-letter answer is treated as one "
    "token, so {'AB'} matches neither A nor B and scores 0. Unreachable from "
    "the live pipeline (it always joins with commas) but reachable via "
    "imported data. Fix planned with majority_vote/parse_choice_id cleanup."
), strict=True)
def test_commaless_multiletter_answer_should_score():
    assert score_sc_mc_percent("AB", "A,B") == 100.0


# ─────────────────────────────────────────────────────────────────────────────
# gold_set
# ─────────────────────────────────────────────────────────────────────────────

def test_gold_set_splits_and_normalises():
    assert gold_set("a, c") == ["A", "C"]
    assert gold_set("A,B,C") == ["A", "B", "C"]


def test_gold_set_does_not_split_on_semicolon():
    """gold_set splits on ',' only — a ';' gold is one bogus token.

    This is why check_field_consistency emits a GOLD warning for ';' golds;
    the parser deliberately does not paper over it.
    """
    assert gold_set("A;B") == ["A;B"]


# ─────────────────────────────────────────────────────────────────────────────
# parse_choice_id (single_choice)
# ─────────────────────────────────────────────────────────────────────────────

def test_parse_choice_id_extracts_the_letter():
    assert parse_choice_id("B", valid=A_E) == "B"
    assert parse_choice_id("Die Antwort ist B", valid=A_E) == "B"


def test_parse_choice_id_ignores_invalid_letters():
    assert parse_choice_id("Z", valid=A_E) is None
    assert parse_choice_id("", valid=A_E) is None


@pytest.mark.xfail(reason=(
    "Known latent bug: returns the FIRST letter found, so a negating answer "
    "resolves to the rejected option. 0 occurrences in the live DB today."
), strict=True)
def test_parse_choice_id_should_not_take_the_negated_letter():
    assert parse_choice_id("A ist falsch, B ist richtig", valid=A_E) == "B"


# ─────────────────────────────────────────────────────────────────────────────
# majority_vote
# ─────────────────────────────────────────────────────────────────────────────

def test_majority_vote_picks_the_repeated_answer():
    assert majority_vote(["A", "B", "A"]) == "A"


def test_majority_vote_ignores_blanks():
    assert majority_vote(["", None, "C"]) == "C"
    assert majority_vote(["", None]) == ""


def test_majority_vote_breaks_ties_toward_the_first_trial():
    assert majority_vote(["A", "B", "C"]) == "A"


@pytest.mark.xfail(reason=(
    "Known latent bug: votes on comma-joined strings, so 'A,C' and 'C,A' count "
    "as different answers and a true set-majority can lose. Should vote on the "
    "letter SET. 0 occurrences in the live DB today."
), strict=True)
def test_majority_vote_should_be_order_insensitive_for_multi_choice():
    assert set(majority_vote(["A,C", "A,B", "B,A"]).split(",")) == {"A", "B"}


# ─────────────────────────────────────────────────────────────────────────────
# parse_tolerance / parse_number
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("raw,expected", [
    ("+/- 1",    1.0),
    ("+/-1",     1.0),
    ("± 5",      5.0),
    ("+/- 0,01", 0.01),
    ("0.5",      0.5),
    ("1,5",      1.5),
    (1.0,        1.0),
    (5,          5.0),
])
def test_tolerance_formats_used_by_the_ground_truth_sheets(raw, expected):
    """The sheets write "+/- 1" etc. Bare float() rejects those, and the old
    importer swallowed the ValueError and stored NULL — leaving the judge with
    no tolerance band on 170 open_numeric tasks while the sheet looked filled.
    """
    assert parse_tolerance(raw) == expected


@pytest.mark.parametrize("raw", [None, "", "abc", "n/a"])
def test_unparseable_tolerance_is_none(raw):
    assert parse_tolerance(raw) is None


@pytest.mark.parametrize("raw,expected", [
    ("1.234,56 EUR", 1234.56),   # German decimal comma
    ("1,234.56",     1234.56),   # US decimal point
    ("1 000",        1000.0),    # space as thousands separator
    ("42",           42.0),
    ("-7,5",         -7.5),
])
def test_parse_number_handles_mixed_locale_formats(raw, expected):
    assert parse_number(raw) == expected


def test_parse_number_german_thousands_is_ambiguous():
    """Documents a known wart rather than asserting the ideal.

    "5.000" is five thousand in German but parses as 5.0, because a lone '.'
    is treated as a decimal point. Only reached via parse_tolerance's fallback
    for non-numeric tolerance strings, so impact is limited — but if tolerances
    like "+/- 5.000" ever appear, this needs revisiting.
    """
    assert parse_number("5.000") == 5.0


def test_parse_number_returns_none_without_digits():
    assert parse_number("keine Angabe") is None
    assert parse_number("") is None


# ─────────────────────────────────────────────────────────────────────────────
# build_judge_prompt — the numeric tolerance band
# ─────────────────────────────────────────────────────────────────────────────

TOLERANCE_MARKER = "NUMERISCHE TOLERANZ"


def _judge_prompt(numeric_tol):
    return build_judge_prompt(
        "Ermitteln Sie den Auszahlungsbetrag.",
        "Der Auszahlungsbetrag beträgt € 2.853,13.",
        "2853.12",
        grading_criteria="Akzeptiere EUR-Betrag mit 2 Dezimalstellen.",
        numeric_tol=numeric_tol,
    )


def test_tolerance_band_is_emitted_whenever_a_tolerance_is_given():
    """The band used to be gated on kind == "open_numeric" at the call site.

    189 of the 227 tasks that define a tolerance are journal_entry or open_text,
    so their band was silently dropped and the judge graded numeric answers
    freehand: 2.853,13 against gold 2853.12 (tolerance ±1) scored 100 for
    claude-opus-5 and 0 for gpt-5.6-sol in the same task.
    """
    prompt = _judge_prompt(1.0)
    assert f"{TOLERANCE_MARKER}: ±1.0" in prompt


def test_no_tolerance_block_when_tolerance_is_absent():
    """Tasks without a tolerance must build exactly the prompt they did before
    the fix — the change may only ever add the block, never alter anything else.
    """
    assert TOLERANCE_MARKER not in _judge_prompt(None)


def test_sheet_tolerance_strings_survive_into_the_judge_prompt():
    """End-to-end guard: the sheets write "+/- 1", parse_tolerance turns that
    into 1.0, and it must reach the judge as a band rather than being lost on
    the way (the two halves of this bug were fixed in separate passes).
    """
    prompt = _judge_prompt(parse_tolerance("+/- 1"))
    assert f"{TOLERANCE_MARKER}: ±1.0" in prompt


def test_unparseable_tolerance_yields_no_band():
    """parse_tolerance returns None for junk, which must degrade to "no band"
    rather than crashing the judge call or emitting "±None".
    """
    prompt = _judge_prompt(parse_tolerance("ca. eins"))
    assert TOLERANCE_MARKER not in prompt
    assert "None" not in prompt


# ─────────────────────────────────────────────────────────────────────────────
# Model registry wiring
# ─────────────────────────────────────────────────────────────────────────────

def test_all_models_fallback_is_resolvable():
    """ALL_MODELS is used whenever OPENAI_MODEL_LIST is unset (e.g. the web
    submission path). A name missing from the registry 404s, gets skipped, and
    aborts the whole run with IncompleteRunError — previously true for
    'grok-4-fast' and 'DeepSeek-V3.2-2'.
    """
    unresolvable = [m for m in ALL_MODELS if m not in MODEL_REGISTRY]
    assert unresolvable == [], (
        f"ALL_MODELS entries missing from MODEL_REGISTRY_JSON: {unresolvable}"
    )
