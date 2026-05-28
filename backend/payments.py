"""
AccountingBench — Payments Router (Phase 7 — Stripe Checkout)
==============================================================
POST /submissions/{id}/confirm-payment
  - Called by results.html after Stripe redirects back to the site.
  - Verifies the Checkout Session with Stripe, marks the submission as paid,
    and triggers the benchmark pipeline as a background task.

Flow:
  1. User submits upload form → prepare_submission creates task + Stripe session
  2. User is redirected to Stripe Checkout (hosted page)
  3. After payment, Stripe redirects to results.html?submission=N&stripe_session=cs_...
  4. results.html calls POST /submissions/N/confirm-payment with {session_id}
  5. This endpoint verifies with Stripe, marks paid, triggers pipeline
  6. results.html polls GET /submissions/N/status until done
"""

import logging
import os

import stripe
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.database import get_db
from backend.limiter import limiter, LIMIT_PAYMENT
from backend.models import BenchmarkTask, Submission

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/submissions/{submission_id}/confirm-payment", tags=["Payments"])
@limiter.limit(LIMIT_PAYMENT)
async def confirm_payment(
    request: Request,
    submission_id: int,
    payload: dict,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Verifies a completed Stripe Checkout Session and triggers the benchmark pipeline.

    Body: {"session_id": "cs_test_..."}

    Idempotent — safe to call multiple times (e.g. on page refresh after payment).
    Returns {"ok": True} if payment was already confirmed on a previous call.
    """
    session_id = (payload.get("session_id") or "").strip()
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required.")

    # Load submission — must belong to the authenticated user
    submission = db.query(Submission).filter_by(
        id=submission_id, user_id=user_id
    ).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found.")

    # Idempotent: already confirmed → pipeline already triggered, just return ok
    if submission.payment_status == "paid":
        return {"ok": True, "already_paid": True}

    # Retrieve Stripe secret key
    stripe_key = os.environ.get("STRIPE_SECRET_KEY", "").strip()
    if not stripe_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment service is not configured. Please contact support.",
        )

    # Retrieve and verify the Checkout Session from Stripe
    try:
        session = stripe.checkout.Session.retrieve(session_id, api_key=stripe_key)
    except Exception as e:
        logger.error(f"Stripe session retrieval failed for submission {submission_id}: {e}")
        raise HTTPException(
            status_code=402,
            detail="Could not verify payment with Stripe. Please contact support.",
        )

    if session.payment_status != "paid":
        raise HTTPException(
            status_code=402,
            detail=f"Payment not completed (Stripe status: {session.payment_status}).",
        )

    # Prevent session substitution — metadata must match this submission
    if str(getattr(session.metadata, "submission_id", "")) != str(submission_id):
        raise HTTPException(
            status_code=403,
            detail="Payment session does not match this submission.",
        )

    # Mark submission as paid and ready for processing
    submission.payment_status    = "paid"
    submission.stripe_payment_id = session.payment_intent
    submission.price_charged     = session.amount_total
    submission.status            = "processing"

    # Move task into the admin review queue (was "awaiting_payment")
    task = db.query(BenchmarkTask).filter_by(id=submission.task_id).first()
    if task and task.validation_status == "awaiting_payment":
        task.validation_status = "pending"

    db.commit()

    logger.info(
        f"Payment confirmed — submission {submission_id}, "
        f"PI: {session.payment_intent}, amount: {session.amount_total} {session.currency.upper()}"
    )

    # Trigger the benchmark pipeline as a background task
    # ⚠️  TESTING: uses dummy_pipeline which always returns 100%.
    # ⚠️  PRODUCTION: change this import to backend.processing.pipeline
    from backend.processing.dummy_pipeline import run_pipeline
  #  from backend.processing.pipeline import run_pipeline
    background_tasks.add_task(run_pipeline, submission_id)

    return {"ok": True}
