"""
Option-text answer recovery and raw-response logging.

Both exist because of the same incident: `gpt-5.6-terra` returned a valid
response to a RICHTIG/FALSCH task, the parser could not turn it into a letter,
and the pipeline stored an empty answer scored 0% — which in the database is
indistinguishable from the model answering incorrectly. The raw response was
never persisted, so the actual text could not be recovered afterwards.
"""

import json

import pytest

from backend.processing.pipeline import (
    UnparseableAnswerError,
    _match_option_text,
    log_raw_response,
    parse_choice_id,
    parse_choice_set,
)

# The exact shape that triggered the incident: option VALUES are the words a
# model is most likely to echo instead of the letter.
TRUE_FALSE = {"a": "RICHTIG", "b": "FALSCH"}
A_B = ["A", "B"]


# ─────────────────────────────────────────────────────────────────────────────
# Recovering an answer that quotes the option text
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("answer,expected", [
    ("RICHTIG", "A"),
    ("FALSCH",  "B"),
    ("richtig", "A"),          # case-insensitive
    ("  RICHTIG  ", "A"),      # whitespace-insensitive
])
def test_single_choice_recovers_answer_given_as_option_text(answer, expected):
    """The prompt never says to answer with the letter, so "RICHTIG" is a
    compliant reply. It must resolve rather than being thrown away."""
    assert parse_choice_id(answer, valid=A_B, options=TRUE_FALSE) == expected


def test_multi_choice_recovers_answer_given_as_option_text():
    assert parse_choice_set("FALSCH", valid=A_B, options=TRUE_FALSE) == ["B"]


def test_letter_answer_still_wins_over_text_matching():
    """Letter extraction runs first; the fallback must not override it."""
    assert parse_choice_id("B", valid=A_B, options=TRUE_FALSE) == "B"


def test_partial_or_substring_text_is_rejected():
    """Only exact matches. A truncated echo must not resolve to an option —
    guessing here would silently fabricate an answer."""
    for answer in ["RICHT", "RICHTIGE", "nicht richtig", "un-richtig"]:
        assert parse_choice_id(answer, valid=A_B, options=TRUE_FALSE) is None


def test_ambiguous_text_match_is_rejected():
    """Two options with identical text cannot be disambiguated, so neither wins."""
    dupes = {"a": "GLEICH", "b": "GLEICH"}
    assert parse_choice_id("GLEICH", valid=A_B, options=dupes) is None
    assert _match_option_text("GLEICH", dupes) is None


def test_text_match_respects_valid_choices():
    """An option whose letter is not in valid_choices must not be returned."""
    assert parse_choice_id("RICHTIG", valid=["B"], options=TRUE_FALSE) is None


def test_answer_matching_no_option_still_returns_nothing():
    """This is the case that must reach UnparseableAnswerError, not a 0% score."""
    assert parse_choice_id("wahr", valid=A_B, options=TRUE_FALSE) is None
    assert parse_choice_set("keine Angabe", valid=A_B, options=TRUE_FALSE) == []


def test_missing_or_malformed_options_are_handled():
    for opts in (None, {}, "not a dict", []):
        assert _match_option_text("RICHTIG", opts) is None


def test_behaviour_without_options_is_unchanged():
    """Existing call sites pass no options; those paths must behave as before."""
    assert parse_choice_id("A", valid=A_B) == "A"
    assert parse_choice_id("RICHTIG", valid=A_B) is None
    assert parse_choice_set("A,B", valid=A_B) == ["A", "B"]


# ─────────────────────────────────────────────────────────────────────────────
# UnparseableAnswerError
# ─────────────────────────────────────────────────────────────────────────────

def test_unparseable_answer_error_is_a_runtime_error():
    """It must be caught by run_single_model's generic `except Exception`, which
    is what routes the model to ERROR and prevents a row being written."""
    assert issubclass(UnparseableAnswerError, RuntimeError)


# ─────────────────────────────────────────────────────────────────────────────
# Raw-response logging
# ─────────────────────────────────────────────────────────────────────────────

def test_log_raw_response_writes_one_jsonl_record(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.processing.pipeline.RAW_RESPONSE_LOG_DIR", str(tmp_path))
    monkeypatch.setattr("backend.processing.pipeline.RAW_RESPONSE_LOG_ENABLED", True)

    log_raw_response(
        {"run_id": "run_test_1", "task_id": 2, "phase": "trial_1",
         "kind": "single_choice", "valid_choices": ["A", "B"]},
        "gpt-5.6-terra",
        raw_text='{"answer": "RICHTIG", "confidence": 0.99}',
        answer="",
        conf=0.99,
        tokens=(138, 185, 162),
    )

    path = tmp_path / "raw_responses_run_test_1.jsonl"
    assert path.exists()
    rec = json.loads(path.read_text(encoding="utf-8").strip())
    assert rec["task_id"] == 2
    assert rec["model"] == "gpt-5.6-terra"
    assert rec["phase"] == "trial_1"
    assert rec["valid_choices"] == ["A", "B"]
    assert rec["raw"] == '{"answer": "RICHTIG", "confidence": 0.99}'
    assert rec["parsed_answer"] == ""          # the discarded-answer signature
    assert rec["token_reasoning"] == 162


def test_log_raw_response_appends_rather_than_overwriting(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.processing.pipeline.RAW_RESPONSE_LOG_DIR", str(tmp_path))
    monkeypatch.setattr("backend.processing.pipeline.RAW_RESPONSE_LOG_ENABLED", True)
    ctx = {"run_id": "run_test_2", "task_id": 1}
    for phase in ("trial_1", "trial_2", "trial_3", "consolidation", "judge"):
        log_raw_response(dict(ctx, phase=phase), "m", "raw", "A", 0.5)

    lines = (tmp_path / "raw_responses_run_test_2.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 5
    assert [json.loads(l)["phase"] for l in lines] == [
        "trial_1", "trial_2", "trial_3", "consolidation", "judge"
    ]


def test_log_raw_response_preserves_german_characters(tmp_path, monkeypatch):
    """Windows defaults to cp1252, which would mangle the corpus."""
    monkeypatch.setattr("backend.processing.pipeline.RAW_RESPONSE_LOG_DIR", str(tmp_path))
    monkeypatch.setattr("backend.processing.pipeline.RAW_RESPONSE_LOG_ENABLED", True)
    german = "Die Aufwertung über die fortgeführten Anschaffungskosten ist größer – 1.234,56 €"
    log_raw_response({"run_id": "run_de", "task_id": 3}, "m", german, german, 0.9)

    rec = json.loads((tmp_path / "raw_responses_run_de.jsonl").read_text(encoding="utf-8").strip())
    assert rec["raw"] == german


def test_log_raw_response_never_raises_on_a_bad_path(monkeypatch):
    """Logging must not be able to abort a benchmark run."""
    monkeypatch.setattr("backend.processing.pipeline.RAW_RESPONSE_LOG_ENABLED", True)
    monkeypatch.setattr(
        "backend.processing.pipeline.RAW_RESPONSE_LOG_DIR", "\0:/definitely/not/writable"
    )
    log_raw_response({"run_id": "x", "task_id": 1}, "m", "raw")  # must not raise


def test_log_raw_response_respects_the_disable_switch(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.processing.pipeline.RAW_RESPONSE_LOG_DIR", str(tmp_path))
    monkeypatch.setattr("backend.processing.pipeline.RAW_RESPONSE_LOG_ENABLED", False)
    log_raw_response({"run_id": "run_off", "task_id": 1}, "m", "raw")
    assert list(tmp_path.iterdir()) == []


def test_log_raw_response_handles_missing_context(tmp_path, monkeypatch):
    """A call site that passes no context must still produce a usable record."""
    monkeypatch.setattr("backend.processing.pipeline.RAW_RESPONSE_LOG_DIR", str(tmp_path))
    monkeypatch.setattr("backend.processing.pipeline.RAW_RESPONSE_LOG_ENABLED", True)
    log_raw_response(None, "m", "raw", "A", 0.5)

    rec = json.loads((tmp_path / "raw_responses_unknown_run.jsonl").read_text(encoding="utf-8").strip())
    assert rec["model"] == "m"
    assert rec["run_id"] is None
