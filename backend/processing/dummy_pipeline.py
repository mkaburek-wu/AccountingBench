"""
AccountingBench — Dummy Pipeline (Testing Only)
================================================
Placeholder for the real benchmark script. Used during development so
the full submission → result flow can be tested without calling any AI APIs.

Results are saved to the database only (benchmark_runs and benchmark_outputs
tables). The frontend pulls scores from the database via the status endpoint —
the script never runs again once results are stored.

What this does:
  1. Sets submission status → "processing"
  2. Waits 3 seconds to simulate script runtime
  3. Inserts one BenchmarkRun + one BenchmarkOutput per model (score = 100%)
  4. Sets submission status → "done"

SWAPPING IN THE REAL SCRIPT:
  Replace this file with backend/processing/pipeline.py.
  Keep the same function signature:
      run_pipeline(submission_id: int, db: Session = None) -> None
  The database inserts follow the same pattern — just replace the dummy
  answers and scores with real model outputs.
"""

import logging
import time
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models import BenchmarkOutput, BenchmarkRun, BenchmarkTask, Submission

logger = logging.getLogger(__name__)

# ── Fixed model list ──────────────────────────────────────────────────────────
# Keep this in sync with the real pipeline when you swap it in.
ALL_MODELS = [
    "gpt-5.4",
    "gpt-5.2",
    "claude-opus-4-6",
    "claude-sonnet-4-6",
    "gpt-5-mini",
    "Mistral-Large-3",
    "grok-4-fast",
    "gpt-4o",
    "DeepSeek-V3.2-2",
    "mercury-2",
]


def run_pipeline(submission_id: int, db: Session = None) -> None:
    """
    Dummy pipeline — always returns 100% for every model.
    Saves results to benchmark_runs and benchmark_outputs in the database.

    Called as a FastAPI BackgroundTask from submissions.py:
        background_tasks.add_task(run_pipeline, submission.id)

    Args:
        submission_id: The ID of the Submission row to process.
        db:            Optional — if None a new session is created internally.
    """
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        # ── 1. Mark as processing ─────────────────────────────────────────────
        submission = db.query(Submission).filter_by(id=submission_id).first()
        if not submission:
            logger.error(f"Submission {submission_id} not found.")
            return

        submission.status = "processing"
        db.commit()
        logger.info(f"[DUMMY] Submission {submission_id} — processing started.")

        # ── 2. Simulate script runtime ────────────────────────────────────────
        # Remove this sleep when using the real script.
        time.sleep(3)

        # ── 3. Get the task ───────────────────────────────────────────────────
        task = db.query(BenchmarkTask).filter_by(id=submission.task_id).first()
        if not task:
            raise ValueError(f"BenchmarkTask not found for submission {submission_id}")

        # ── 4. Shared run_id for this benchmark run ───────────────────────────
        # All models in a single benchmark run share the same run_id so you
        # can group them together later.
        run_id = (
            f"run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            f"_{uuid.uuid4().hex[:8]}"
        )

        # ── 5. Insert one BenchmarkRun + BenchmarkOutput per model ────────────
        for model_name in ALL_MODELS:

            # Run metadata — one row per model
            run = BenchmarkRun(
                run_id                = run_id,
                task_id               = task.id,
                model_name            = model_name,
                run_timestamp         = datetime.utcnow(),
                temperature           = 0.0,
                n_trials              = 3,
                system_prompt_version = "dummy_v1",
                dataset_version       = "v3",
                judge_model           = "gpt-5-mini",
                inference_notes       = "DUMMY PIPELINE — score always 100%",
            )
            db.add(run)

            # Output — one row per model with all scores and answers
            # The real pipeline fills these with actual model responses.
            output = BenchmarkOutput(
                run_id               = run_id,
                task_id              = task.id,
                model_name           = model_name,

                # Three dummy trial answers
                model_answer_1       = "DUMMY_ANSWER",
                model_confidence_1   = 1.0,
                model_answer_2       = "DUMMY_ANSWER",
                model_confidence_2   = 1.0,
                model_answer_3       = "DUMMY_ANSWER",
                model_confidence_3   = 1.0,

                # Consolidated answer
                final_answer         = "DUMMY_ANSWER",
                avg_model_confidence = 1.0,

                # Scores — always 100% in the dummy pipeline
                # The real pipeline computes these from model responses.
                final_score_percent  = 100.0,
                score_percent_sc_mc  = 100.0,
                judge_score_percent  = None,
                judge_confidence     = None,

                # Metadata
                evaluation_method    = "dummy",
                evaluated_at_utc     = datetime.utcnow(),
                evaluation_notes     = "Dummy pipeline — always returns 100%.",
            )
            db.add(output)

        db.commit()
        logger.info(
            f"[DUMMY] Submission {submission_id} — "
            f"{len(ALL_MODELS)} model outputs saved to database."
        )

        # ── 6. Mark as done ───────────────────────────────────────────────────
        submission = db.query(Submission).filter_by(id=submission_id).first()
        submission.status       = "done"
        submission.completed_at = datetime.utcnow()
        db.commit()
        logger.info(f"[DUMMY] Submission {submission_id} — done.")

    except Exception as e:
        logger.error(f"[DUMMY] Submission {submission_id} — error: {e}", exc_info=True)
        try:
            sub = db.query(Submission).filter_by(id=submission_id).first()
            if sub:
                sub.status       = "error"
                sub.completed_at = datetime.utcnow()
                db.commit()
        except Exception:
            pass

    finally:
        if close_db:
            db.close()
