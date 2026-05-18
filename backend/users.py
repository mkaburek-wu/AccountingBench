"""
AccountingBench — User Account Endpoint
========================================
DELETE /users/me — permanently deletes the user's account.

Deletion order (to respect FK constraints):
  1. BenchmarkOutput rows for the user's tasks
  2. BenchmarkRun rows for the user's tasks
  3. Submission rows for the user
  4. BenchmarkTask rows submitted by the user
  5. User row
  6. Clerk user via Clerk Backend API
"""

import logging
import os

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.database import get_db
from backend.models import BenchmarkOutput, BenchmarkRun, BenchmarkTask, Submission, User

logger = logging.getLogger(__name__)
router = APIRouter()


@router.delete("/users/me", tags=["Users"])
async def delete_account(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Permanently deletes the current user's account.
    Removes all local DB records first, then deletes the user from Clerk.
    """
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    # Collect IDs of tasks submitted by this user
    task_ids = [
        row.id for row in
        db.query(BenchmarkTask.id)
        .filter_by(submitted_by=user_id, source="user_submitted")
        .all()
    ]

    # Delete benchmark outputs and runs that reference the user's tasks
    if task_ids:
        db.query(BenchmarkOutput).filter(
            BenchmarkOutput.task_id.in_(task_ids)
        ).delete(synchronize_session=False)
        db.query(BenchmarkRun).filter(
            BenchmarkRun.task_id.in_(task_ids)
        ).delete(synchronize_session=False)

    # Delete submissions (references both user and tasks)
    db.query(Submission).filter_by(user_id=user_id).delete(synchronize_session=False)

    # Delete tasks
    if task_ids:
        db.query(BenchmarkTask).filter(
            BenchmarkTask.id.in_(task_ids)
        ).delete(synchronize_session=False)

    # Delete user row
    db.delete(user)
    db.commit()
    logger.info(f"Deleted local data for user {user_id}")

    # Delete from Clerk (best-effort — local DB is already clean)
    clerk_secret = os.environ.get("CLERK_SECRET_KEY", "").strip()
    if clerk_secret:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.delete(
                    f"https://api.clerk.com/v1/users/{user_id}",
                    headers={"Authorization": f"Bearer {clerk_secret}"},
                )
                if resp.status_code not in (200, 204):
                    logger.error(
                        f"Clerk delete failed for {user_id}: "
                        f"{resp.status_code} {resp.text}"
                    )
                else:
                    logger.info(f"Deleted Clerk user {user_id}")
        except Exception as e:
            logger.error(f"Clerk delete error for {user_id}: {e}")

    return {"ok": True}
