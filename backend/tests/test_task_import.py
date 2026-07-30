"""
Task import path (backend/batch_run.py upsert_task).

Uses a throwaway in-memory SQLite database — never the project database — so
these stay fast and side-effect free while still exercising the real import
code rather than a reimplementation of it.

The tolerance assertions matter most: the ground-truth sheets express
tolerances as "+/- 1", bare float() rejects that, and the original importer
caught the ValueError and stored NULL. That silently stripped the judge's
tolerance band from 170 open_numeric tasks while the source sheet still looked
correctly populated — invisible in every score and every log.
"""

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.batch_run import upsert_task
from backend.models import Base, BenchmarkTask


@pytest.fixture
def db():
    """A fresh in-memory database with the real schema."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _row(**overrides):
    row = {
        "question_id": "t_0001",
        "task_type": "calculation",
        "prompt": "Berechnen Sie den Kapitalwert.",
        "answer_type": "open_numeric",
        "gold_answer": "1234,56",
        "regulatory_framework": "IFRS",
        "category": "financial_accounting",
        "education_level": "professional_examinations",
        "numeric_tolerance": "+/- 1",
        "grading_criteria": "rubric",
        "options": None,
    }
    row.update(overrides)
    return pd.Series(row)


@pytest.mark.parametrize("raw,expected", [
    ("+/- 1",    1.0),
    ("+/-1",     1.0),
    ("± 5",      5.0),
    ("+/- 0,01", 0.01),
    ("0.5",      0.5),
    (1.0,        1.0),
])
def test_annotated_tolerances_survive_import(db, raw, expected):
    task = upsert_task(db, _row(numeric_tolerance=raw), approved=True, user_id=None)
    assert task.numeric_tolerance == expected, (
        f"tolerance {raw!r} was lost on import — the judge would get no "
        f"tolerance band for this task"
    )


@pytest.mark.parametrize("raw", [None, "", "keine Angabe"])
def test_missing_or_unparseable_tolerance_becomes_none(db, raw):
    task = upsert_task(db, _row(numeric_tolerance=raw), approved=True, user_id=None)
    assert task.numeric_tolerance is None


def test_approved_flag_sets_public_and_status(db):
    task = upsert_task(db, _row(), approved=True, user_id=None)
    assert task.is_public is True
    assert task.validation_status == "approved"
    assert task.source == "batch_import"


def test_not_approved_stays_private(db):
    task = upsert_task(db, _row(validation_status="pending"), approved=False, user_id=None)
    assert task.is_public is False
    assert task.validation_status == "pending"


def test_upsert_updates_in_place_rather_than_duplicating(db):
    """Re-importing a question_id must update the existing task, never insert a
    second row — question_id is the natural key the whole pipeline joins on."""
    upsert_task(db, _row(prompt="original"), approved=True, user_id=None)
    upsert_task(db, _row(prompt="corrected"), approved=True, user_id=None)

    tasks = db.query(BenchmarkTask).filter_by(question_id="t_0001").all()
    assert len(tasks) == 1
    assert tasks[0].prompt == "corrected"


def test_choice_options_are_parsed_into_a_letter_dict(db):
    task = upsert_task(
        db,
        _row(answer_type="multi_choice", gold_answer="A,B",
             options="A) first\nB) second"),
        approved=True, user_id=None,
    )
    assert task.options == {"A": "first", "B": "second"}


def test_regulatory_year_is_coerced_to_int(db):
    task = upsert_task(
        db, _row(applicable_regulatory_year=2018.0), approved=True, user_id=None
    )
    assert task.applicable_regulatory_year == 2018
