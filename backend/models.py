"""
AccountingBench — Database Models
==================================
All six tables for the submission portal.

Run migrations after any change to this file:
    alembic revision --autogenerate -m "describe your change"
    alembic upgrade head
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, Column, DateTime, Float, ForeignKey,
    Integer, JSON, String, Text
)
from sqlalchemy.orm import DeclarativeBase, relationship


# ── Base class all models inherit from ───────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ─────────────────────────────────────────────────────────────────────────────
#  TABLE 1 — users
#  Populated on first login via Clerk. We never store passwords here.
# ─────────────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id         = Column(String, primary_key=True)   # Clerk user ID, e.g. "user_2abc..."
    email      = Column(String, unique=True, nullable=False)
    first_name = Column(String, nullable=True)
    last_name  = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active  = Column(Boolean, default=True, nullable=False)
    # Set to False to block a user without deleting their data

    # Relationships
    submissions = relationship("Submission", back_populates="user")
    tasks       = relationship("BenchmarkTask", back_populates="submitted_by_user")


# ─────────────────────────────────────────────────────────────────────────────
#  TABLE 2 — allowed_domains
#  Managed via the Clerk dashboard (no-code) or via admin API endpoints.
#  Example row: domain = "kpmg.com"
# ─────────────────────────────────────────────────────────────────────────────
class AllowedDomain(Base):
    __tablename__ = "allowed_domains"

    id       = Column(Integer, primary_key=True, autoincrement=True)
    domain   = Column(String, unique=True, nullable=False)  # e.g. "kpmg.com"
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    added_by = Column(String, nullable=True)                # admin email for audit trail


# ─────────────────────────────────────────────────────────────────────────────
#  TABLE 3 — benchmark_tasks
#  Replaces the ground-truth Excel spreadsheet.
#  The original 520 tasks are imported here with source="original_dataset".
#  Every user-contributed task is added here with source="user_submitted".
#
#  Column names match the ground-truth spreadsheet exactly so the Python
#  script can consume rows from this table without changes to its logic.
# ─────────────────────────────────────────────────────────────────────────────
class BenchmarkTask(Base):
    __tablename__ = "benchmark_tasks"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(String, unique=True, nullable=False)
    # Auto-generated on insert, e.g. "q_0521". Must be unique across all tasks.

    # ── Core question fields (match ground-truth spreadsheet columns) ─────────
    prompt      = Column(Text, nullable=False)
    # The full question text sent to the models.

    answer_type = Column(String, nullable=False)
    # One of: single_choice | multi_choice | open_text | open_numeric | journal_entry

    task_type   = Column(String, nullable=False)
    # One of: interpretation_of_law | calculation | journal_entry

    task_format = Column(String, nullable=True)
    # Optional secondary format descriptor.

    gold_answer = Column(Text, nullable=False)
    # The correct answer.
    # For choice tasks: "A" or "A,C" (comma-separated for multi_choice).
    # For open tasks: the reference answer text.
    # For open_numeric: the numeric value as a string.

    options     = Column(JSON, nullable=True)
    # Answer options for choice tasks.
    # Stored as a JSON dict: {"A": "option text", "B": "option text", ...}
    # Null for open-text/numeric/journal-entry tasks.

    grading_criteria = Column(Text, nullable=True)
    # Rubric used by the LLM judge for open-text and journal-entry tasks.
    # Null for choice and numeric tasks.

    numeric_tolerance = Column(Float, nullable=True)
    # Acceptable +/- tolerance band for open_numeric tasks.
    # Example: 1.0 means answers within ±1 of gold_answer are accepted.
    # Null for all other task types.

    acceptable_variants = Column(Text, nullable=True)
    # Pipe-separated list of alternative valid answers, if any.

    # ── Context and attachments ───────────────────────────────────────────────
    context        = Column(Text, nullable=True)
    # Optional background text provided to the model alongside the question.

    attached_files = Column(Text, nullable=True)
    # URL or file path reference to supporting documents.
    # Actual uploaded files are stored on disk; paths saved in Submission.

    # ── Regulatory and domain metadata ───────────────────────────────────────
    regulatory_framework       = Column(String, nullable=False)
    # One of: Austrian Tax Law | IFRS | National GAAP |
    #         Mixed Accounting Framework | Mixed: Accounting + Tax

    applicable_regulatory_year = Column(Integer, nullable=True)
    # The year the regulation applies, e.g. 2024.

    category    = Column(String, nullable=False)
    # One of: Tax | Financial Accounting | Management Accounting

    subcategory = Column(String, nullable=True)

    skills      = Column(String, nullable=True)
    # Comma-separated competency tags.

    education_level = Column(String, nullable=False)
    # One of: Professional Examinations | University Master's | Secondary Vocational

    notes = Column(Text, nullable=True)
    # Additional notes for reviewers.

    # ── Provenance and review ─────────────────────────────────────────────────
    source = Column(String, nullable=False, default="user_submitted")
    # "original_dataset" for the initial 520 tasks.
    # "user_submitted" for all user contributions.

    submitted_by = Column(String, ForeignKey("users.id"), nullable=True)
    # Null for the original 520 tasks.

    is_public = Column(Boolean, default=False, nullable=False)
    # False until you approve the task.
    # True = included in public leaderboard calculations.
    # The original 520 tasks are imported with is_public=True.

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    validated_by      = Column(String, nullable=True)   # your admin email after review
    validation_status = Column(String, default="pending", nullable=False)
    # One of: pending | approved | rejected
    # "approved" on original 520 tasks, "pending" on new submissions until you review.

    # ── Uploaded file paths ───────────────────────────────────────────────────
    pdf_path   = Column(String, nullable=True)
    # Server path to the uploaded PDF, e.g. "uploads/user_2abc/42/document.pdf"

    excel_path = Column(String, nullable=True)
    # Server path to the uploaded Excel file.

    # Relationships
    submitted_by_user = relationship("User", back_populates="tasks")
    runs              = relationship("BenchmarkRun", back_populates="task")
    outputs           = relationship("BenchmarkOutput", back_populates="task")
    submission        = relationship("Submission", back_populates="task", uselist=False)


# ─────────────────────────────────────────────────────────────────────────────
#  TABLE 4 — benchmark_runs
#  One row per model per task execution.
#  Mirrors the "Runs" sheet from the existing Excel pipeline.
# ─────────────────────────────────────────────────────────────────────────────
class BenchmarkRun(Base):
    __tablename__ = "benchmark_runs"

    id      = Column(Integer, primary_key=True, autoincrement=True)
    run_id  = Column(String, nullable=False, index=True)
    # UUID string, e.g. "run_20260415_143022_a1b2c3d4"
    # Same run_id is shared across all models for one task execution.

    task_id = Column(Integer, ForeignKey("benchmark_tasks.id"), nullable=False)

    model_name = Column(String, nullable=False)
    # e.g. "gpt-5.4", "claude-opus-4-6" etc.

    run_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    temperature           = Column(Float, default=0.0)
    n_trials              = Column(Integer, default=3)
    system_prompt_version = Column(String, nullable=True)   # e.g. "v3_types"
    dataset_version       = Column(String, nullable=True)   # e.g. "v3"
    judge_model           = Column(String, nullable=True)   # always "gpt-5-mini"
    inference_notes       = Column(Text, nullable=True)

    # Relationships
    task    = relationship("BenchmarkTask", back_populates="runs")
    outputs = relationship("BenchmarkOutput", back_populates="run",
                           foreign_keys="BenchmarkOutput.run_id",
                           primaryjoin="BenchmarkRun.run_id == BenchmarkOutput.run_id")


# ─────────────────────────────────────────────────────────────────────────────
#  TABLE 5 — benchmark_outputs
#  One row per model per task. Stores all trial answers, scores, and
#  judge output. Mirrors the "Outputs" sheet from the Excel pipeline.
# ─────────────────────────────────────────────────────────────────────────────
class BenchmarkOutput(Base):
    __tablename__ = "benchmark_outputs"

    id      = Column(Integer, primary_key=True, autoincrement=True)
    run_id  = Column(String, nullable=False, index=True)
    # Matches BenchmarkRun.run_id — links output to its run metadata.

    task_id    = Column(Integer, ForeignKey("benchmark_tasks.id"), nullable=False)
    model_name = Column(String, nullable=False)

    # ── Three trial answers ───────────────────────────────────────────────────
    model_answer_1    = Column(Text, nullable=True)
    model_confidence_1 = Column(Float, nullable=True)
    model_answer_2    = Column(Text, nullable=True)
    model_confidence_2 = Column(Float, nullable=True)
    model_answer_3    = Column(Text, nullable=True)
    model_confidence_3 = Column(Float, nullable=True)

    # ── Consolidated answer ───────────────────────────────────────────────────
    final_answer        = Column(Text, nullable=True)
    # Majority vote for choice tasks.
    # Consolidation call result for open/numeric/journal tasks.

    avg_model_confidence = Column(Float, nullable=True)

    # ── Scores ────────────────────────────────────────────────────────────────
    score_percent_sc_mc = Column(Float, nullable=True)
    # SC/MC formula score. Only set for single_choice and multi_choice tasks.
    # Formula: (100/c * correct) - (100/c * incorrect)

    judge_score_percent = Column(Float, nullable=True)
    # LLM-as-a-judge score (0–100).
    # Only set for open_text, open_numeric, and journal_entry tasks.

    judge_confidence    = Column(Float, nullable=True)
    # Judge's self-reported confidence.

    final_score_percent = Column(Float, nullable=True)
    # The score that counts for the leaderboard.
    # For choice tasks:  equals score_percent_sc_mc.
    # For open tasks:    equals judge_score_percent.

    # ── Evaluation metadata ───────────────────────────────────────────────────
    evaluation_method = Column(String, nullable=True)
    # "sc_mc_formula" or "judge"

    token_input     = Column(Integer, nullable=True)
    token_output    = Column(Integer, nullable=True)
    token_reasoning = Column(Integer, nullable=True)
    # Token counts from trial 1 only (as in the original script).

    evaluated_at_utc   = Column(DateTime, default=datetime.utcnow)
    evaluation_notes   = Column(Text, nullable=True)

    # Relationships
    task = relationship("BenchmarkTask", back_populates="outputs")
    run  = relationship("BenchmarkRun", back_populates="outputs",
                        foreign_keys=[run_id],
                        primaryjoin="BenchmarkOutput.run_id == BenchmarkRun.run_id")


# ─────────────────────────────────────────────────────────────────────────────
#  TABLE 6 — submissions
#  Tracks each user's contribution from form submission through
#  payment, script execution, and admin review.
# ─────────────────────────────────────────────────────────────────────────────
class Submission(Base):
    __tablename__ = "submissions"

    id      = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("benchmark_tasks.id"), nullable=True)
    # Null briefly between form submission and task insertion.
    # Set as soon as the task row is created.

    status = Column(String, default="pending", nullable=False)
    # pending → processing → done → error
    # Updated by the pipeline wrapper as the script runs.

    # ── Payment fields (Phase 2 — included now so no migration needed later) ──
    payment_status    = Column(String, default="unpaid", nullable=False)
    # unpaid → paid → refunded

    stripe_payment_id = Column(String, nullable=True)
    # Stripe Payment Intent ID, e.g. "pi_3abc..."
    # Used to issue refunds if the script fails after payment.

    price_charged     = Column(Integer, nullable=True)
    # Amount charged in cents, e.g. 5000 = €50.00.
    # Copied from settings.price_per_submission at time of payment.

    # ── Timestamps ────────────────────────────────────────────────────────────
    submitted_at  = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at  = Column(DateTime, nullable=True)
    # Set when status changes to "done" or "error".

    # Relationships
    user = relationship("User", back_populates="submissions")
    task = relationship("BenchmarkTask", back_populates="submission")


# ─────────────────────────────────────────────────────────────────────────────
#  TABLE 7 — settings
#  Single-row configuration table.
#  Change the price here without touching any code.
#  Initialise with one row: INSERT INTO settings (id) VALUES (1);
# ─────────────────────────────────────────────────────────────────────────────
class Settings(Base):
    __tablename__ = "settings"

    id                   = Column(Integer, primary_key=True, default=1)
    # Always 1. This table has exactly one row.

    price_per_submission = Column(Integer, nullable=True)
    # Price in cents. Set this after measuring your average API cost per task.
    # Example: 5000 = €50.00.
    # Phase 2 only — leave null until Stripe is integrated.

    currency             = Column(String, nullable=True, default="eur")
    # ISO currency code. Phase 2 only.

    updated_at           = Column(DateTime, default=datetime.utcnow,
                                  onupdate=datetime.utcnow, nullable=False)
