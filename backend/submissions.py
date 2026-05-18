"""
AccountingBench — Submissions Endpoint
========================================
Handles the upload form submission:
  1. Validates all required fields and uploaded files.
  2. Generates a unique question_id for the new task.
  3. Saves uploaded files to disk.
  4. Inserts the task into benchmark_tasks.
  5. Creates a Submission row to track progress.
  6. Triggers the benchmark pipeline as a FastAPI BackgroundTask.

The pipeline runs asynchronously — the endpoint returns immediately with
the submission_id, and the frontend polls GET /submissions/{id}/status
every 3 seconds until status = "done".

SWAPPING THE REAL SCRIPT:
  Currently uses backend/processing/dummy_pipeline.py which always returns
  100% for every model. When you are ready to use the real benchmark script,
  change the import at the bottom of this file:

    # Testing (current):
    from backend.processing.dummy_pipeline import run_pipeline

    # Production (real script):
    from backend.processing.pipeline import run_pipeline

  Everything else stays the same.
"""

import logging
import os
import uuid
from datetime import datetime
from pathlib import Path

import stripe as _stripe
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.database import get_db, SessionLocal
from backend.models import BenchmarkTask, Submission, Settings

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Upload directory ──────────────────────────────────────────────────────────
# Files are saved to UPLOAD_DIR/{user_id}/{submission_id}/filename
# Set UPLOAD_DIR in your .env file. Defaults to ./uploads next to this file.
UPLOAD_DIR = Path(os.environ.get("UPLOAD_DIR", "./uploads"))

# ── File size limit: 20 MB ────────────────────────────────────────────────────
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB in bytes

# ── Allowed MIME types ────────────────────────────────────────────────────────
ALLOWED_PDF_TYPES   = {"application/pdf"}
ALLOWED_EXCEL_TYPES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "application/vnd.ms-excel",                                           # .xls
    "application/octet-stream",                                           # some browsers send this
}
ALLOWED_PDF_EXTENSIONS   = {".pdf"}
ALLOWED_EXCEL_EXTENSIONS = {".xlsx", ".xls"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _generate_question_id(db: Session) -> str:
    """
    Generates a unique question_id for a new user-submitted task.
    Format: usr_{6-char hex}  e.g. "usr_3a9f12"
    Checks the database to guarantee uniqueness.
    """
    for _ in range(10):
        candidate = f"usr_{uuid.uuid4().hex[:6]}"
        exists = db.query(BenchmarkTask).filter_by(question_id=candidate).first()
        if not exists:
            return candidate
    # Fallback to full UUID if all short IDs collide (extremely unlikely)
    return f"usr_{uuid.uuid4().hex[:12]}"


def _validate_file(
    upload: UploadFile,
    allowed_extensions: set,
    allowed_mime_types: set,
    field_name: str,
) -> None:
    """
    Validates an uploaded file by checking its extension and MIME type.
    Raises HTTPException(400) if validation fails.
    """
    if not upload or not upload.filename:
        return  # Optional file — skip validation if not provided

    ext = Path(upload.filename).suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid file type for {field_name}: '{upload.filename}'. "
                f"Allowed extensions: {', '.join(sorted(allowed_extensions))}"
            ),
        )

    if upload.content_type and upload.content_type not in allowed_mime_types:
        # Some browsers send "application/octet-stream" for Excel — allow it
        # but only if the extension is correct (already checked above).
        if upload.content_type != "application/octet-stream":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Invalid MIME type for {field_name}: '{upload.content_type}'. "
                    f"Please upload a valid {field_name} file."
                ),
            )


async def _save_file(upload: UploadFile, dest_dir: Path, prefix: str) -> str:
    """
    Reads an uploaded file and saves it to dest_dir.
    Returns the saved file path as a string, or empty string if no file.
    Raises HTTPException(400) if the file exceeds MAX_FILE_SIZE.
    Raises HTTPException(500) if the file cannot be written.
    """
    if not upload or not upload.filename:
        return ""

    dest_dir.mkdir(parents=True, exist_ok=True)

    # Read the file content
    content = await upload.read()

    # Check file size
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"File '{upload.filename}' is too large "
                f"({len(content) // (1024*1024)} MB). Maximum allowed size is 20 MB."
            ),
        )

    # Build a safe filename: prefix_originalname (spaces replaced with underscores)
    safe_name = upload.filename.replace(" ", "_")
    dest_path = dest_dir / f"{prefix}_{safe_name}"

    try:
        dest_path.write_bytes(content)
    except Exception as e:
        logger.error(f"Failed to save file {dest_path}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not save the uploaded file. Please try again.",
        )

    logger.info(f"Saved file: {dest_path} ({len(content)} bytes)")
    return str(dest_path)


# ── Background task: Stripe Checkout Session creation ─────────────────────────

def _create_stripe_session(
    submission_id: int,
    question_id: str,
    price: int,
    currency: str,
    frontend_url: str,
    stripe_key: str,
) -> None:
    """
    Creates a Stripe Checkout Session in a background thread and saves the URL
    to the submission row. Runs after the HTTP response has already been sent,
    so it never blocks the browser connection.
    """
    db = SessionLocal()
    try:
        _stripe.api_key = stripe_key
        checkout = _stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency":     currency,
                    "product_data": {
                        "name":        "AccountingBench Task Submission",
                        "description": f"Task {question_id} — benchmark evaluation across all models",
                    },
                    "unit_amount": price,
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=(
                f"{frontend_url}/auth-pages/payment-success.html"
                f"?submission={submission_id}"
                f"&stripe_session={{CHECKOUT_SESSION_ID}}"
            ),
            cancel_url=f"{frontend_url}/auth-pages/upload.html?cancelled=1",
            metadata={"submission_id": str(submission_id)},
        )
        submission = db.query(Submission).filter_by(id=submission_id).first()
        if submission:
            submission.checkout_url = checkout.url
            db.commit()
        logger.info(f"Checkout Session created for submission {submission_id} ({question_id})")
    except Exception as e:
        logger.error(f"Stripe session creation failed for submission {submission_id}: {e}")
    finally:
        db.close()


# ── Main submission endpoint ──────────────────────────────────────────────────

@router.post("/submissions/prepare", tags=["Submissions"])
async def prepare_submission(
    background_tasks: BackgroundTasks,
    db:      Session = Depends(get_db),
    user_id: str     = Depends(get_current_user),

    # ── Required text fields ──────────────────────────────────────────────────
    prompt:                    str = Form(...),
    answer_type:               str = Form(...),
    task_type:                 str = Form(...),
    gold_answer:               str = Form(...),
    category:                  str = Form(...),
    regulatory_framework:      str = Form(...),
    applicable_regulatory_year:str = Form(...),
    education_level:           str = Form(...),

    # ── Optional text fields ──────────────────────────────────────────────────
    options:           str = Form(default=""),
    grading_criteria:  str = Form(default=""),
    numeric_tolerance: str = Form(default=""),
    context:           str = Form(default=""),
    subcategory:       str = Form(default=""),
    notes:             str = Form(default=""),

    # ── Optional file uploads ─────────────────────────────────────────────────
    pdf_file:   UploadFile = File(default=None),
    excel_file: UploadFile = File(default=None),
):
    """
    Receives the upload form, saves the task and files, then triggers
    the benchmark pipeline as a background task.

    Returns immediately with {"submission_id": int, "task_id": int}.
    The frontend polls GET /submissions/{id}/status to track progress.
    """

    # ── 1. Validate enum fields ───────────────────────────────────────────────
    valid_answer_types = {"single_choice", "multi_choice", "open_text", "open_numeric", "journal_entry"}
    valid_task_types   = {"interpretation_of_law", "calculation", "journal_entry"}
    valid_categories   = {"tax", "financial_accounting", "management_accounting"}
    valid_edu_levels   = {"professional_examinations", "university_masters", "secondary_vocational"}
    valid_frameworks   = {
        "austrian_tax_law", "ifrs", "national_gaap",
        "mixed_accounting_framework", "mixed_accounting_tax",
    }

    if answer_type not in valid_answer_types:
        raise HTTPException(400, f"Invalid answer_type: '{answer_type}'.")
    if task_type not in valid_task_types:
        raise HTTPException(400, f"Invalid task_type: '{task_type}'.")
    if category not in valid_categories:
        raise HTTPException(400, f"Invalid category: '{category}'.")
    if education_level not in valid_edu_levels:
        raise HTTPException(400, f"Invalid education_level: '{education_level}'.")
    if regulatory_framework not in valid_frameworks:
        raise HTTPException(400, f"Invalid regulatory_framework: '{regulatory_framework}'.")

    # ── 2. Validate conditional required fields ───────────────────────────────
    if answer_type in {"single_choice", "multi_choice"} and not options.strip():
        raise HTTPException(400, "options is required for choice tasks.")
    if answer_type in {"open_text", "journal_entry", "open_numeric"} and not grading_criteria.strip():
        raise HTTPException(400, "grading_criteria is required for open-ended tasks.")

    # ── 3. Parse numeric_tolerance ────────────────────────────────────────────
    tolerance_float = None
    if numeric_tolerance.strip():
        try:
            tolerance_float = float(numeric_tolerance.strip())
        except ValueError:
            raise HTTPException(400, "numeric_tolerance must be a number, e.g. 1.00")

    # ── 4. Parse applicable_regulatory_year ───────────────────────────────────
    try:
        reg_year = int(applicable_regulatory_year.strip())
    except ValueError:
        raise HTTPException(400, "applicable_regulatory_year must be a whole number, e.g. 2026")

    # ── 5. Validate uploaded files ────────────────────────────────────────────
    if pdf_file and pdf_file.filename:
        _validate_file(pdf_file, ALLOWED_PDF_EXTENSIONS, ALLOWED_PDF_TYPES, "PDF")
    if excel_file and excel_file.filename:
        _validate_file(excel_file, ALLOWED_EXCEL_EXTENSIONS, ALLOWED_EXCEL_TYPES, "Excel")

    # ── 6. Generate question_id ───────────────────────────────────────────────
    question_id = _generate_question_id(db)

    # Check Stripe availability before creating DB records
    stripe_key = os.environ.get("STRIPE_SECRET_KEY", "").strip()

    # ── 7. Create the task row ────────────────────────────────────────────────
    task = BenchmarkTask(
        question_id                = question_id,
        prompt                     = prompt.strip(),
        answer_type                = answer_type,
        task_type                  = task_type,
        task_format                = answer_type,       # mirrors answer_type for compatibility
        gold_answer                = gold_answer.strip(),
        options                    = options.strip()           or None,
        grading_criteria           = grading_criteria.strip() or None,
        numeric_tolerance          = tolerance_float,
        context                    = context.strip()          or None,
        subcategory                = subcategory.strip()      or None,
        notes                      = notes.strip()            or None,
        regulatory_framework       = regulatory_framework,
        applicable_regulatory_year = reg_year,
        category                   = category,
        education_level            = education_level,
        source                     = "user_submitted",
        submitted_by               = user_id,
        is_public                  = False,          # private until admin approves
        validation_status          = "awaiting_payment" if stripe_key else "pending",
        created_at                 = datetime.utcnow(),
    )
    db.add(task)
    db.flush()   # assigns task.id without committing — so we can use it below

    # ── 8. Create the submission tracking row ─────────────────────────────────
    submission = Submission(
        user_id        = user_id,
        task_id        = task.id,
        status         = "pending",
        payment_status = "unpaid",   # Phase 2: Stripe will set this to "paid"
        submitted_at   = datetime.utcnow(),
    )
    db.add(submission)
    db.flush()   # assigns submission.id

    # ── 9. Save uploaded files ────────────────────────────────────────────────
    upload_dir = UPLOAD_DIR / user_id / str(submission.id)
    timestamp  = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    pdf_path   = await _save_file(pdf_file,   upload_dir, f"{timestamp}_pdf")
    excel_path = await _save_file(excel_file, upload_dir, f"{timestamp}_excel")

    # Update task with file paths
    if pdf_path:   task.pdf_path   = pdf_path
    if excel_path: task.excel_path = excel_path

    # ── 10. Commit everything ─────────────────────────────────────────────────
    db.commit()
    logger.info(
        f"Submission {submission.id} created — "
        f"task {task.id} ({question_id}) by user {user_id}"
    )

    # ── 11. Trigger pipeline (dev) or queue Stripe session creation (prod) ───────
    if not stripe_key:
        # Dev fallback: no Stripe configured → run benchmark immediately
        # ⚠️  TESTING: uses dummy_pipeline which always returns 100%.
        # ⚠️  PRODUCTION: change this import to backend.processing.pipeline
        from backend.processing.dummy_pipeline import run_pipeline
        # from backend.processing.pipeline import run_pipeline
        background_tasks.add_task(run_pipeline, submission.id)
    else:
        settings     = db.query(Settings).filter_by(id=1).first()
        price        = settings.price_per_submission if (settings and settings.price_per_submission) else 5000
        currency     = settings.currency             if (settings and settings.currency)             else "eur"
        frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:5500").rstrip("/")

        # Stripe session is created in a background task so the HTTP response
        # is returned to the browser immediately (avoids TCP connection drops
        # caused by the ~1 second Stripe API call blocking the response).
        background_tasks.add_task(
            _create_stripe_session,
            submission.id, question_id, price, currency, frontend_url, stripe_key,
        )

    return {
        "submission_id": submission.id,
        "task_id":       task.id,
        "question_id":   question_id,
        "checkout_url":  None,  # frontend polls /submissions/{id}/status for this
    }
