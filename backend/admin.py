"""
AccountingBench — Admin Endpoints
===================================
New admin endpoints that complement the existing ones in main.py:
  GET  /admin/stats               — aggregate counts for the dashboard
  GET  /admin/users               — list all users with submission counts
  POST /admin/users/{id}/activate   — re-enable a deactivated account
  POST /admin/users/{id}/deactivate — block a user without deleting data
"""

import logging
import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.auth import require_admin
from backend.database import get_db
from backend.models import BenchmarkTask, Submission, User

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/admin/stats", tags=["Admin"])
async def admin_stats(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Aggregate counts for the admin stats tab."""
    week_ago  = datetime.utcnow() - timedelta(days=7)
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # Task counts (user-submitted only)
    total_tasks = db.query(BenchmarkTask).filter_by(source="user_submitted").count()
    pending     = db.query(BenchmarkTask).filter_by(source="user_submitted", validation_status="pending").count()
    approved    = db.query(BenchmarkTask).filter_by(source="user_submitted", validation_status="approved").count()
    rejected    = db.query(BenchmarkTask).filter_by(source="user_submitted", validation_status="rejected").count()

    # User counts
    total_users  = db.query(User).count()
    active_users = db.query(User).filter_by(is_active=True).count()

    # Submission counts
    total_subs      = db.query(Submission).count()
    subs_today      = db.query(Submission).filter(Submission.submitted_at >= today_start).count()
    subs_week       = db.query(Submission).filter(Submission.submitted_at >= week_ago).count()
    subs_processing = db.query(Submission).filter_by(status="processing").count()

    # Revenue (paid submissions)
    paid_rows       = db.query(Submission).filter_by(payment_status="paid").all()
    revenue_cents   = sum(s.price_charged or 0 for s in paid_rows)

    return {
        "tasks": {
            "total":    total_tasks,
            "pending":  pending,
            "approved": approved,
            "rejected": rejected,
        },
        "users": {
            "total":  total_users,
            "active": active_users,
        },
        "submissions": {
            "total":      total_subs,
            "today":      subs_today,
            "this_week":  subs_week,
            "processing": subs_processing,
            "paid":       len(paid_rows),
        },
        "revenue": {
            "total_cents": revenue_cents,
            "currency":    "eur",
        },
    }


@router.get("/admin/users", tags=["Admin"])
async def list_users(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Returns all registered users with their submission counts."""
    users = db.query(User).order_by(User.created_at.desc()).all()
    result = []
    for u in users:
        sub_count = db.query(Submission).filter_by(user_id=u.id).count()
        result.append({
            "id":               u.id,
            "email":            u.email,
            "first_name":       u.first_name,
            "last_name":        u.last_name,
            "created_at":       u.created_at.isoformat() if u.created_at else None,
            "is_active":        u.is_active,
            "submission_count": sub_count,
        })
    return result


@router.post("/admin/users/{user_id}/deactivate", tags=["Admin"])
async def deactivate_user(
    user_id: str,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Blocks a user from accessing the platform without deleting their data."""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    admin_email = os.environ.get("ADMIN_EMAIL", "").strip()
    if user.email == admin_email:
        raise HTTPException(status_code=400, detail="Cannot deactivate the admin account.")
    user.is_active = False
    db.commit()
    logger.info(f"User {user.email} deactivated by admin {admin_id}")
    return {"ok": True}


@router.post("/admin/users/{user_id}/activate", tags=["Admin"])
async def activate_user(
    user_id: str,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Re-enables a previously deactivated user account."""
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user.is_active = True
    db.commit()
    logger.info(f"User {user.email} activated by admin {admin_id}")
    return {"ok": True}
