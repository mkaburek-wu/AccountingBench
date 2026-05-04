"""
AccountingBench — Batch Runner
==============================
Reads tasks from an Excel file (same format as the ground-truth template),
inserts them into benchmark_tasks, creates a submission for each, and runs
the full benchmark pipeline — all without going through the web UI or Clerk.

Usage (run from the accountingbench/ root):
    python -m backend.batch_run --file path/to/tasks.xlsx
    python -m backend.batch_run --file path/to/tasks.xlsx --sheet Questions
    python -m backend.batch_run --file path/to/tasks.xlsx --dry-run
    python -m backend.batch_run --file path/to/tasks.xlsx --sequential

Options:
    --file          Path to the Excel file (required)
    --sheet         Sheet name to read (default: Questions)
    --user          User ID to attribute submissions to (default: BATCH_USER_ID
                    from .env, falls back to "batch_admin")
    --dry-run       Parse and validate the Excel without writing to DB or
                    running any models
    --sequential    Run tasks one after another (default: all in parallel
                    across tasks, models within each task already parallel)
    --skip-existing Skip tasks whose question_id already exists in DB
                    (default: update the task row and re-run models)
    --approved      Mark imported tasks as validation_status=approved and
                    is_public=True immediately (default: pending + False)

Expected Excel columns (all others are ignored):
    question_id, task_type, task_format, prompt, options, context,
    answer_type, gold_answer, acceptable_variants, grading_criteria,
    numeric_tolerance, regulatory_framework, applicable_regulatory_year,
    category, subcategory, skills, education_level, notes,
    validated_by, validation_status
"""

import argparse
import json
import re
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv

# Load .env from the project root (accountingbench/.env)
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(_root, ".env"))

from backend.database import SessionLocal
from backend.models import BenchmarkTask, Submission, User
from backend.processing.pipeline import run_pipeline

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("batch_run")
# Enable DEBUG logging for the pipeline (same as main.py does for the web server)
#logging.getLogger("backend.processing.pipeline").setLevel(logging.DEBUG)

# ── Constants ─────────────────────────────────────────────────────────────────
BATCH_USER_ID = os.environ.get("BATCH_USER_ID", "batch_admin")
BATCH_USER_EMAIL = os.environ.get("BATCH_USER_EMAIL", "batch@accountingbench.local")

# Default uploads folder — same as the web upload path
DEFAULT_UPLOADS_DIR = os.path.join(_root, "backend", "uploads")

# Columns we read from the Excel (all optional except the starred ones)
EXCEL_COLUMNS = [
    "question_id",           # * required — must be unique
    "task_type",             # * required
    "task_format",
    "prompt",                # * required
    "options",
    "context",
    "answer_type",           # * required
    "gold_answer",           # * required
    "acceptable_variants",
    "grading_criteria",
    "numeric_tolerance",
    "regulatory_framework",  # * required
    "applicable_regulatory_year",
    "category",              # * required
    "subcategory",
    "skills",
    "education_level",       # * required
    "notes",
    "validated_by",
    "validation_status",
]

REQUIRED_COLUMNS = [
    "question_id", "task_type", "prompt", "answer_type",
    "gold_answer", "regulatory_framework", "category", "education_level",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def safe(val, default=""):
    """Return string value or default for NaN/None."""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return default
    return str(val).strip()


def parse_options(raw) -> dict | None:
    """
    Options column may be:
      - a JSON string: {"a": "text", "b": "text"}
      - a pipe-separated string: "a) text | b) text | c) text"
      - NaN / empty
    Returns a dict or None.
    """
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    s = str(raw).strip()
    if not s:
        return None

    # Try JSON first
    try:
        parsed = json.loads(s)
        if isinstance(parsed, dict):
            return parsed
    except (json.JSONDecodeError, ValueError):
        pass

    # Try pipe-separated "a) text | b) text" format
    if "|" in s:
        result = {}
        for part in s.split("|"):
            part = part.strip()
            if part and len(part) > 2 and part[1] == ")":
                key = part[0].lower()
                val = part[2:].strip()
                result[key] = val
        if result:
            return result

    # Store as-is under key "raw" so nothing is lost
    return {"raw": s}


def resolve_attached_files(raw, uploads_dir):
    """
    Given the attached_files cell value from the Excel, find the actual
    file(s) on disk and return a pipe-separated string of absolute paths
    suitable for the pipeline's resolve_attached_documents_text().

    Supports:
      - Filenames only:     "document.pdf"
      - Relative paths:     "uploads/document.pdf"
      - Absolute paths:     "C:\\...\\document.pdf"  (used as-is if exists)
      - Multiple files:     "doc1.pdf | doc2.pdf"
      - URLs (http/https):  passed through unchanged
      - NaN / empty:        returns None
    """
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    s = str(raw).strip()
    if not s:
        return None

    resolved = []
    for entry in s.split("|"):
        entry = entry.strip()
        if not entry:
            continue

        # URLs pass through unchanged — pipeline will download them
        if re.match(r"^https?://", entry, re.IGNORECASE):
            resolved.append(entry)
            logger.info(f"    Attached file (URL): {entry}")
            continue

        # Absolute path — use as-is if it exists
        if os.path.isabs(entry) and os.path.exists(entry):
            resolved.append(entry)
            logger.info(f"    Attached file (absolute): {entry}")
            continue

        # Relative path or bare filename — search in uploads_dir
        # 1. Try it directly relative to uploads_dir
        candidate = os.path.join(uploads_dir, entry)
        if os.path.exists(candidate):
            resolved.append(os.path.abspath(candidate))
            logger.info(f"    Attached file found: {candidate}")
            continue

        # 2. Try bare filename only (strip any directory prefix from the entry)
        filename = os.path.basename(entry)
        candidate2 = os.path.join(uploads_dir, filename)
        if os.path.exists(candidate2):
            resolved.append(os.path.abspath(candidate2))
            logger.info(f"    Attached file found: {candidate2}")
            continue

        # 3. Search recursively under uploads_dir
        found = None
        for root, _, files in os.walk(uploads_dir):
            if filename in files:
                found = os.path.join(root, filename)
                break
        if found:
            resolved.append(os.path.abspath(found))
            logger.info(f"    Attached file found (recursive search): {found}")
            continue

        # Not found — warn but keep the raw entry so pipeline logs the error
        logger.warning(f"    Attached file NOT found: \'{entry}\' (searched in {uploads_dir})")
        resolved.append(entry)

    return " | ".join(resolved) if resolved else None


def ensure_batch_user(db) -> str:
    """
    Make sure the batch user exists in the users table.
    Returns the user ID.
    """
    user = db.query(User).filter_by(id=BATCH_USER_ID).first()
    if not user:
        user = User(
            id=BATCH_USER_ID,
            email=BATCH_USER_EMAIL,
            first_name="Batch",
            last_name="Runner",
        )
        db.add(user)
        db.commit()
        logger.info(f"Created batch user: {BATCH_USER_ID}")
    return BATCH_USER_ID


def read_excel(file_path: str, sheet_name: str) -> pd.DataFrame:
    """Read and validate the Excel file."""
    logger.info(f"Reading {file_path} — sheet '{sheet_name}'")
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
    except Exception as e:
        logger.error(f"Could not read Excel file: {e}")
        sys.exit(1)

    # Check required columns exist
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        logger.error(f"Excel is missing required columns: {missing}")
        logger.error(f"Found columns: {list(df.columns)}")
        sys.exit(1)

    logger.info(f"Found {len(df)} row(s) to process.")
    return df


def upsert_task(db, row: pd.Series, approved: bool, user_id: str, uploads_dir: str = None) -> BenchmarkTask:
    """
    Insert a new task or update the existing one (matched by question_id).
    Returns the BenchmarkTask ORM object.
    """
    qid = safe(row.get("question_id"))
    if not qid:
        raise ValueError("Row has no question_id — cannot upsert.")

    task = db.query(BenchmarkTask).filter_by(question_id=qid).first()

    fields = dict(
        prompt                    = safe(row.get("prompt")),
        answer_type               = safe(row.get("answer_type")),
        task_type                 = safe(row.get("task_type")),
        task_format               = safe(row.get("task_format")) or None,
        gold_answer               = safe(row.get("gold_answer")),
        options                   = parse_options(row.get("options")),
        grading_criteria          = safe(row.get("grading_criteria")) or None,
        acceptable_variants       = safe(row.get("acceptable_variants")) or None,
        context                   = safe(row.get("context")) or None,
        attached_files            = resolve_attached_files(
            row.get("attached_files"), uploads_dir
        ) if uploads_dir else safe(row.get("attached_files")) or None,
        regulatory_framework      = safe(row.get("regulatory_framework")),
        applicable_regulatory_year= (
            int(row["applicable_regulatory_year"])
            if pd.notna(row.get("applicable_regulatory_year", float("nan")))
            else None
        ),
        category                  = safe(row.get("category")),
        subcategory               = safe(row.get("subcategory")) or None,
        skills                    = safe(row.get("skills")) or None,
        education_level           = safe(row.get("education_level")),
        notes                     = safe(row.get("notes")) or None,
        source                    = "batch_import",
        submitted_by              = user_id,
        is_public                 = approved,
        validation_status         = "approved" if approved else safe(row.get("validation_status")) or "pending",
        validated_by              = safe(row.get("validated_by")) or None,
    )

    # numeric_tolerance
    tol_raw = row.get("numeric_tolerance")
    if pd.notna(tol_raw) if isinstance(tol_raw, float) else tol_raw is not None:
        try:
            fields["numeric_tolerance"] = float(tol_raw)
        except (TypeError, ValueError):
            fields["numeric_tolerance"] = None
    else:
        fields["numeric_tolerance"] = None

    if task:
        # Update existing row
        for k, v in fields.items():
            setattr(task, k, v)
        logger.info(f"  Updated existing task: {qid}")
    else:
        # Insert new row
        task = BenchmarkTask(question_id=qid, **fields)
        db.add(task)
        logger.info(f"  Inserted new task: {qid}")

    db.commit()
    db.refresh(task)
    return task


def create_submission(db, task: BenchmarkTask, user_id: str) -> Submission:
    """Create a new pending submission for the task."""
    sub = Submission(
        user_id      = user_id,
        task_id      = task.id,
        status       = "pending",
        payment_status = "unpaid",
        submitted_at = datetime.utcnow(),
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    logger.info(f"  Created submission {sub.id} for task {task.question_id}")
    return sub


def process_row(row: pd.Series, args, user_id: str, index: int = 0, total: int = 0) -> dict:
    """
    Full lifecycle for one Excel row:
      1. Upsert task into DB
      2. Create submission
      3. Run pipeline (blocks until all models finish)
    Returns a result dict for reporting.
    """
    qid = safe(row.get("question_id"))
    prefix = f"[{index}/{total}]" if total else ""
    result = {"question_id": qid, "status": "unknown", "submission_id": None, "error": None}

    db = SessionLocal()
    try:
        # Skip if exists and --skip-existing
        if args.skip_existing:
            existing = db.query(BenchmarkTask).filter_by(question_id=qid).first()
            if existing:
                logger.info(f"{prefix} [SKIP] {qid} — already exists.")
                result["status"] = "skipped"
                return result

        # 1. Upsert task
        logger.info(f"{prefix} ── Task: {qid} ──────────────────────────────")
        task = upsert_task(db, row, approved=args.approved, user_id=user_id, uploads_dir=args.uploads_dir)

        # 2. Create submission
        sub = create_submission(db, task, user_id)
        result["submission_id"] = sub.id

        # 3. Run pipeline (pipeline manages its own sessions per thread)
        db.close()  # Close this session before pipeline opens new ones
        db = None

        logger.info(f"{prefix} [RUN] {qid} → submission {sub.id} — starting pipeline...")
        run_pipeline(sub.id)
        logger.info(f"{prefix} [DONE] {qid} → submission {sub.id} — pipeline complete.")
        result["status"] = "done"

    except Exception as e:
        logger.error(f"{prefix} [ERROR] {qid}: {e}", exc_info=True)
        result["status"] = "error"
        result["error"] = str(e)
    finally:
        if db:
            db.close()

    return result


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="AccountingBench batch runner — import tasks from Excel and run benchmarks."
    )
    parser.add_argument("--file",          required=True,  help="Path to Excel file")
    parser.add_argument("--sheet",         default="Questions", help="Sheet name (default: Questions)")
    parser.add_argument("--user",          default=None,   help="User ID to attribute submissions to")
    parser.add_argument("--dry-run",       action="store_true", help="Parse Excel only, no DB writes")
    parser.add_argument("--sequential",    action="store_true", help="Run tasks one by one (default: parallel)")
    parser.add_argument("--max-workers",   type=int, default=4, help="Max parallel tasks (default: 10, use 1 for sequential)")
    parser.add_argument("--skip-existing", action="store_true", help="Skip tasks already in DB")
    parser.add_argument("--uploads-dir",
                        default=DEFAULT_UPLOADS_DIR,
                        help=f"Folder to search for attached files (default: {DEFAULT_UPLOADS_DIR})")
    parser.add_argument("--approved",      action="store_true", help="Mark tasks as approved + is_public=True")
    args = parser.parse_args()

    # ── Read Excel ────────────────────────────────────────────────────────────
    df = read_excel(args.file, args.sheet)

    # ── Dry run — just print what would happen ────────────────────────────────
    if args.dry_run:
        logger.info("=== DRY RUN — no writes ===")
        for i, (_, row) in enumerate(df.iterrows()):
            qid   = safe(row.get("question_id"))
            ptype = safe(row.get("answer_type"))
            prompt_preview = safe(row.get("prompt"))[:80].replace("\n", " ")
            logger.info(f"  Row {i+1}: {qid} | {ptype} | {prompt_preview}...")
        logger.info(f"=== {len(df)} task(s) would be processed ===")
        return

    # ── Ensure batch user exists ──────────────────────────────────────────────
    user_id = args.user or BATCH_USER_ID
    db = SessionLocal()
    try:
        ensure_batch_user(db)
    finally:
        db.close()

    # ── Process rows ──────────────────────────────────────────────────────────
    rows = [row for _, row in df.iterrows()]
    results = []

    if args.sequential or len(rows) == 1:
        logger.info(f"Running {len(rows)} task(s) sequentially...")
        for i, row in enumerate(rows, start=1):
            logger.info(f"")
            logger.info(f"{'─' * 60}")
            logger.info(f"  Task {i}/{len(rows)}: {safe(row.get('question_id'))}")
            logger.info(f"{'─' * 60}")
            results.append(process_row(row, args, user_id, index=i, total=len(rows)))
    else:
        max_workers = min(args.max_workers, len(rows))
        logger.info(f"Running {len(rows)} task(s) in parallel batches of {max_workers}...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(process_row, row, args, user_id, i + 1, len(rows)): row
                for i, row in enumerate(rows)
            }
            for future in as_completed(futures):
                results.append(future.result())

    # ── Summary ───────────────────────────────────────────────────────────────
    logger.info("")
    logger.info("=" * 60)
    logger.info("BATCH RUN SUMMARY")
    logger.info("=" * 60)

    done     = [r for r in results if r["status"] == "done"]
    skipped  = [r for r in results if r["status"] == "skipped"]
    errors   = [r for r in results if r["status"] == "error"]

    logger.info(f"  Total:   {len(results)}")
    logger.info(f"  Done:    {len(done)}")
    logger.info(f"  Skipped: {len(skipped)}")
    logger.info(f"  Errors:  {len(errors)}")

    if done:
        logger.info("")
        logger.info("Completed submissions:")
        for r in done:
            logger.info(f"  {r['question_id']} → submission {r['submission_id']}")

    if errors:
        logger.info("")
        logger.info("Errors:")
        for r in errors:
            logger.info(f"  {r['question_id']}: {r['error']}")

    logger.info("=" * 60)


if __name__ == "__main__":
    main()
