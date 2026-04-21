"""
AccountingBench — FastAPI Application Entry Point
===================================================
This is the main file that starts the server and registers all routes.

How to run locally (from the root accountingbench/ folder, venv active):
    uvicorn backend.main:app --reload

Then open:
    http://localhost:8000          → API root (health check)
    http://localhost:8000/docs     → Interactive API documentation (very useful for testing)
    http://localhost:8000/redoc    → Alternative API documentation

File structure this depends on:
    backend/
    ├── main.py            ← this file
    ├── auth.py            ← Clerk JWT verification + domain check
    ├── database.py        ← DB engine and session
    ├── models.py          ← SQLAlchemy table definitions
    ├── submissions.py     ← upload form endpoints (Phase 3)
    ├── admin.py           ← approve/reject + domain management (Phase 4)
    └── leaderboard.py     ← public aggregate scores (Phase 5)
"""

import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.database import get_db, check_connection, engine
from backend.models import Base, Settings
from backend.auth import get_current_user, require_admin

load_dotenv()

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ── Allowed origins for CORS ──────────────────────────────────────────────────
# These are the URLs that are allowed to make requests to this API.
# In development this is localhost.
# In production add your Render Static Site URLs here.
#
# You can also set this via the environment variable ALLOWED_ORIGINS
# as a comma-separated list:
#   ALLOWED_ORIGINS=https://accountingbench.onrender.com,https://accountingbench-auth.onrender.com

_origins_env = os.environ.get("ALLOWED_ORIGINS", "")
ALLOWED_ORIGINS = (
    [o.strip() for o in _origins_env.split(",") if o.strip()]
    if _origins_env
    else [
        "http://localhost:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:8080",
        # Add your Render Static Site URLs here when you deploy:
        # "https://accountingbench-public.onrender.com",
        # "https://accountingbench-auth.onrender.com",
    ]
)


# ── Lifespan (startup + shutdown) ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs on server startup and shutdown.
    Startup: checks DB connection and creates tables if they don't exist.
    Shutdown: nothing special needed for SQLite/PostgreSQL.
    """
    # ── Startup ───────────────────────────────────────────────────────────────
    logger.info("AccountingBench API starting up...")

    # Check database connection
    try:
        check_connection()
        logger.info("Database connection: OK")
    except Exception as e:
        logger.error(f"Database connection FAILED: {e}")
        raise RuntimeError(f"Cannot connect to database: {e}")

    # Create tables if they don't exist yet
    # (Alembic handles this in production — this is a safety net for dev)
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables: OK")

    # Ensure the settings row exists (always exactly one row with id=1)
    _ensure_settings_row()
    logger.info("Settings row: OK")

    logger.info(f"CORS allowed origins: {ALLOWED_ORIGINS}")
    logger.info("AccountingBench API ready.")

    yield  # Server is running

    # ── Shutdown ──────────────────────────────────────────────────────────────
    logger.info("AccountingBench API shutting down.")


def _ensure_settings_row():
    """Creates the single settings row if it does not exist yet."""
    from backend.database import SessionLocal
    db = SessionLocal()
    try:
        settings = db.query(Settings).filter_by(id=1).first()
        if not settings:
            db.add(Settings(id=1))
            db.commit()
            logger.info("Settings row created.")
    except Exception as e:
        logger.warning(f"Could not ensure settings row: {e}")
    finally:
        db.close()


# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="AccountingBench API",
    description=(
        "Backend API for the AccountingBench submission portal. "
        "Handles authentication, task contributions, benchmark runs, "
        "admin review, and the public leaderboard."
    ),
    version="1.0.0",
    docs_url="/docs",       # Interactive docs at /docs
    redoc_url="/redoc",     # Alternative docs at /redoc
    lifespan=lifespan,
)


# ── CORS middleware ───────────────────────────────────────────────────────────
# Must be added before any routes.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,     # Required for Clerk cookies to be sent cross-origin
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Root endpoint (health check) ──────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    """
    Health check endpoint.
    Returns a simple message confirming the API is running.
    Visit http://localhost:8000 to test.
    """
    return {
        "status":  "ok",
        "message": "AccountingBench API is running.",
        "docs":    "/docs",
    }


@app.get("/health", tags=["Health"])
async def health(db: Session = Depends(get_db)):
    """
    Detailed health check.
    Tests the database connection and returns the API version.
    """
    try:
        check_connection()
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"

    return {
        "api":      "ok",
        "database": db_status,
        "version":  "1.0.0",
    }


# ── User profile endpoint ─────────────────────────────────────────────────────
@app.get("/me", tags=["Users"])
async def get_me(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the currently signed-in user's profile.
    Useful for the frontend to confirm the session is valid and get the user's name.
    """
    from backend.models import User
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return {
        "id":         user.id,
        "email":      user.email,
        "first_name": user.first_name,
        "last_name":  user.last_name,
        "is_active":  user.is_active,
    }


# ── Leaderboard endpoint (public) ─────────────────────────────────────────────
@app.get("/api/leaderboard", tags=["Leaderboard"])
async def get_leaderboard(db: Session = Depends(get_db)):
    """
    Returns the current public leaderboard.
    Calculates average scores per model across all approved (is_public=True) tasks.
    This endpoint is public — no login required.

    Returns the same shape as the old lbData array in data.js so the
    existing renderLeaderboard() and chart functions work without changes.
    """
    from backend.models import BenchmarkTask, BenchmarkOutput
    from collections import defaultdict

    # Get all approved task IDs
    approved_ids = [
        t.id for t in
        db.query(BenchmarkTask.id).filter_by(is_public=True).all()
    ]

    if not approved_ids:
        return []

    # Get all outputs for approved tasks
    outputs = (
        db.query(BenchmarkOutput)
        .filter(BenchmarkOutput.task_id.in_(approved_ids))
        .filter(BenchmarkOutput.final_score_percent.isnot(None))
        .all()
    )

    if not outputs:
        return []

    # Build a lookup of task_id → category
    tasks = {
        t.id: t for t in
        db.query(BenchmarkTask)
        .filter(BenchmarkTask.id.in_(approved_ids))
        .all()
    }

    # Aggregate scores per model, overall and per category
    scores        = defaultdict(list)
    by_category   = defaultdict(lambda: defaultdict(list))
    task_counts   = defaultdict(set)

    for o in outputs:
        task = tasks.get(o.task_id)
        if not task:
            continue
        scores[o.model_name].append(o.final_score_percent)
        by_category[o.model_name][task.category].append(o.final_score_percent)
        task_counts[o.model_name].add(o.task_id)

    def avg(lst):
        return round(sum(lst) / len(lst), 1) if lst else None

    # Build result in the same shape as lbData in data.js
    result = []
    for rank, (model, sc) in enumerate(
        sorted(scores.items(), key=lambda x: -avg(x[1])), start=1
    ):
        result.append({
            "rank":       rank,
            "name":       model,
            "overall":    avg(sc),
            "financial":  avg(by_category[model].get("financial", [])),
            "management": avg(by_category[model].get("management", [])),
            "tax":        avg(by_category[model].get("tax", [])),
            "n":          str(len(task_counts[model])),
        })

    return result


# ── Submissions — "my submissions" endpoint ───────────────────────────────────
@app.get("/submissions/mine", tags=["Submissions"])
async def my_submissions(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the current user's submission history.
    Shown on the landing page.
    Does NOT return result_data — only status and metadata.
    """
    from backend.models import Submission, BenchmarkTask

    submissions = (
        db.query(Submission)
        .filter_by(user_id=user_id)
        .order_by(Submission.submitted_at.desc())
        .all()
    )

    result = []
    for s in submissions:
        task = db.query(BenchmarkTask).filter_by(id=s.task_id).first() if s.task_id else None
        result.append({
            "id":           s.id,
            "status":       s.status,
            "submitted_at": s.submitted_at.isoformat() if s.submitted_at else None,
            "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            "task_preview": task.prompt[:80] + "..." if task and task.prompt else None,
            "task_category": task.category if task else None,
            "payment_status": s.payment_status,
        })

    return result


# ── Submissions — status polling endpoint ─────────────────────────────────────
@app.get("/submissions/{submission_id}/status", tags=["Submissions"])
async def submission_status(
    submission_id: int,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Returns the current status of a submission and, if done, the model scores.
    Polled every 3 seconds by the upload page while the script is running.

    Status values:
        pending    → saved, waiting for payment confirmation (Phase 2)
        processing → Python script is running
        done       → script finished, scores available
        error      → script encountered an error
    """
    from backend.models import Submission, BenchmarkOutput

    submission = db.query(Submission).filter_by(
        id=submission_id, user_id=user_id
    ).first()

    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found.")

    response = {
        "id":     submission.id,
        "status": submission.status,
    }

    # If done, include the model scores
    if submission.status == "done" and submission.task_id:
        outputs = (
            db.query(BenchmarkOutput)
            .filter_by(task_id=submission.task_id)
            .filter(BenchmarkOutput.final_score_percent.isnot(None))
            .order_by(BenchmarkOutput.final_score_percent.desc())
            .all()
        )
        response["model_scores"] = [
            {
                "model":             o.model_name,
                "score":             o.final_score_percent,
                "method":            o.evaluation_method,
                "avg_confidence":    o.avg_model_confidence,
            }
            for o in outputs
        ]

    if submission.status == "error":
        response["error_message"] = (
            "The benchmark script encountered an error processing your task. "
            "Please contact the administrator."
        )

    return response


# ── Admin — list pending tasks ────────────────────────────────────────────────
@app.get("/admin/tasks", tags=["Admin"])
async def list_tasks_for_review(
    status: str = "pending",
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Returns tasks filtered by validation_status.
    Default: status=pending (tasks awaiting your review).
    Use ?status=approved or ?status=rejected to see other groups.
    Admin only.
    """
    from backend.models import BenchmarkTask, BenchmarkOutput

    tasks = (
        db.query(BenchmarkTask)
        .filter_by(validation_status=status)
        .filter(BenchmarkTask.source == "user_submitted")
        .order_by(BenchmarkTask.created_at.desc())
        .all()
    )

    result = []
    for t in tasks:
        # Get the model scores if the script has already run
        outputs = (
            db.query(BenchmarkOutput)
            .filter_by(task_id=t.id)
            .order_by(BenchmarkOutput.final_score_percent.desc())
            .all()
        )
        result.append({
            "id":                   t.id,
            "question_id":          t.question_id,
            "prompt":               t.prompt,
            "answer_type":          t.answer_type,
            "task_type":            t.task_type,
            "category":             t.category,
            "regulatory_framework": t.regulatory_framework,
            "gold_answer":          t.gold_answer,
            "options":              t.options,
            "grading_criteria":     t.grading_criteria,
            "education_level":      t.education_level,
            "notes":                t.notes,
            "pdf_path":             t.pdf_path,
            "excel_path":           t.excel_path,
            "created_at":           t.created_at.isoformat() if t.created_at else None,
            "model_scores": [
                {
                    "model": o.model_name,
                    "score": o.final_score_percent,
                    "method": o.evaluation_method,
                }
                for o in outputs
            ],
        })

    return result


# ── Admin — approve a task ────────────────────────────────────────────────────
@app.post("/admin/tasks/{task_id}/approve", tags=["Admin"])
async def approve_task(
    task_id: int,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Approves a task. Sets is_public=True so it is included in the
    public leaderboard calculations. Admin only.
    """
    from backend.models import BenchmarkTask, User
    from datetime import datetime

    task = db.query(BenchmarkTask).filter_by(id=task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    admin_user = db.query(User).filter_by(id=admin_id).first()

    task.is_public         = True
    task.validation_status = "approved"
    task.validated_by      = admin_user.email if admin_user else admin_id
    db.commit()

    logger.info(f"Task {task_id} ({task.question_id}) approved by {admin_id}")
    return {"ok": True, "task_id": task_id, "status": "approved"}


# ── Admin — reject a task ─────────────────────────────────────────────────────
@app.post("/admin/tasks/{task_id}/reject", tags=["Admin"])
async def reject_task(
    task_id: int,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Rejects a task. Sets is_public=False. The task is not shown on the
    public leaderboard. The user sees status='rejected' on their landing page.
    Admin only.
    """
    from backend.models import BenchmarkTask, User
    from datetime import datetime

    task = db.query(BenchmarkTask).filter_by(id=task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    admin_user = db.query(User).filter_by(id=admin_id).first()

    task.is_public         = False
    task.validation_status = "rejected"
    task.validated_by      = admin_user.email if admin_user else admin_id
    db.commit()

    logger.info(f"Task {task_id} ({task.question_id}) rejected by {admin_id}")
    return {"ok": True, "task_id": task_id, "status": "rejected"}


# ── Admin — list allowed domains ──────────────────────────────────────────────
@app.get("/admin/domains", tags=["Admin"])
async def list_domains(
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Returns all allowed email domains. Admin only."""
    from backend.models import AllowedDomain

    domains = db.query(AllowedDomain).order_by(AllowedDomain.added_at).all()
    return [
        {
            "id":       d.id,
            "domain":   d.domain,
            "added_at": d.added_at.isoformat() if d.added_at else None,
            "added_by": d.added_by,
        }
        for d in domains
    ]


# ── Admin — add an allowed domain ─────────────────────────────────────────────
@app.post("/admin/domains", tags=["Admin"])
async def add_domain(
    payload: dict,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Adds a new allowed email domain.
    Body: {"domain": "kpmg.com"}
    Admin only.
    """
    from backend.models import AllowedDomain, User
    from datetime import datetime

    domain = payload.get("domain", "").strip().lower()
    if not domain:
        raise HTTPException(status_code=400, detail="Domain cannot be empty.")

    # Remove @ if the user typed @kpmg.com instead of kpmg.com
    if domain.startswith("@"):
        domain = domain[1:]

    existing = db.query(AllowedDomain).filter_by(domain=domain).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Domain '{domain}' is already in the allowed list."
        )

    admin_user = db.query(User).filter_by(id=admin_id).first()
    new_domain = AllowedDomain(
        domain   = domain,
        added_at = datetime.now(),
        added_by = admin_user.email if admin_user else admin_id,
    )
    db.add(new_domain)
    db.commit()
    db.refresh(new_domain)

    logger.info(f"Domain '{domain}' added by {admin_id}")
    return {
        "ok":     True,
        "id":     new_domain.id,
        "domain": new_domain.domain,
    }


# ── Admin — remove an allowed domain ─────────────────────────────────────────
@app.delete("/admin/domains/{domain_id}", tags=["Admin"])
async def remove_domain(
    domain_id: int,
    admin_id: str = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Removes an allowed email domain by its ID.
    Get the ID from GET /admin/domains.
    Admin only.
    """
    from backend.models import AllowedDomain

    domain = db.query(AllowedDomain).filter_by(id=domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found.")

    domain_name = domain.domain
    db.delete(domain)
    db.commit()

    logger.info(f"Domain '{domain_name}' removed by {admin_id}")
    return {"ok": True, "removed": domain_name}


# ── Global error handler ──────────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catches any unhandled exception and returns a clean JSON error
    instead of a raw Python traceback.
    """
    logger.error(f"Unhandled error on {request.method} {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An unexpected error occurred. Please try again or contact the administrator."
        },
    )


@app.get("/auth/check-domain", tags=["Auth"])
async def check_domain(domain: str, db: Session = Depends(get_db)):
    """
    Public endpoint — checks if an email domain is in the allowed list.
    Used by the register page to give instant feedback before creating an account.
    """
    from backend.models import AllowedDomain
    allowed = db.query(AllowedDomain).filter_by(domain=domain.lower().strip()).first()
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Domain @{domain} is not authorised."
        )
    return {"ok": True, "domain": domain}