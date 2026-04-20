"""
AccountingBench — One-Time Task Import Script
===============================================
Reads the 521 approved tasks from matrikelnummer_ground_truth_template.xlsx
and inserts them into the benchmark_tasks database table.

Run this ONCE after running:
    alembic upgrade head

How to run (from the backend/ folder with venv active):
    python import_tasks.py

Or with a custom Excel path:
    python import_tasks.py --excel "C:/path/to/matrikelnummer_ground_truth_template.xlsx"

What this script does:
  - Reads only rows where validation_status == "approved"
  - Skips any row that already exists in the database (safe to re-run)
  - Sets is_public = True and source = "original_dataset" for all rows
  - Prints a summary of what was imported and what was skipped
"""

import argparse
import math
import os
import sys
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv

# ── Make sure Python can find the backend package ────────────────────────────
# This allows running the script from inside the backend/ folder.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

load_dotenv()

from backend.database import SessionLocal, engine
from backend.models import Base, BenchmarkTask


# ── Configuration ─────────────────────────────────────────────────────────────
DEFAULT_EXCEL_PATH  = "matrikelnummer_ground_truth_template.xlsx"
SHEET_NAME          = "Questions"
APPROVED_STATUS     = "approved"


# ── Helpers ───────────────────────────────────────────────────────────────────
def clean(value):
    """
    Converts a cell value to a clean Python string or None.
    Handles NaN, float NaN, and empty strings.
    """
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    s = str(value).strip()
    return s if s and s.lower() != "nan" else None


def clean_int(value):
    """
    Converts a cell value to an integer or None.
    The applicable_regulatory_year column comes in as float (e.g. 2026.0).
    """
    if value is None:
        return None
    if isinstance(value, float):
        if math.isnan(value):
            return None
        return int(value)
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def clean_float(value):
    """
    Converts a cell value to a float or None.
    Used for numeric_tolerance.
    """
    if value is None:
        return None
    if isinstance(value, float):
        return None if math.isnan(value) else value
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


# ── Main import function ──────────────────────────────────────────────────────
def import_tasks(excel_path: str):
    print(f"\nAccountingBench — Task Import")
    print(f"{'─' * 50}")
    print(f"Excel file : {os.path.abspath(excel_path)}")
    print(f"Sheet      : {SHEET_NAME}")
    print(f"Database   : {os.environ.get('DATABASE_URL', '(not set)')}")
    print(f"{'─' * 50}\n")

    # ── 1. Check the Excel file exists ────────────────────────────────────────
    if not os.path.exists(excel_path):
        print(f"ERROR: File not found: {excel_path}")
        print("Make sure you are running this script from the backend/ folder,")
        print("or pass the full path with --excel.")
        sys.exit(1)

    # ── 2. Read the Excel file ────────────────────────────────────────────────
    print("Reading Excel file...")
    df = pd.read_excel(excel_path, sheet_name=SHEET_NAME, engine="openpyxl")
    df.columns = [str(c).strip() for c in df.columns]
    print(f"  Total rows in sheet : {len(df)}")

    # ── 3. Filter to approved rows only ───────────────────────────────────────
    approved_df = df[df["validation_status"].astype(str).str.lower() == APPROVED_STATUS.lower()].copy()
    print(f"  Approved rows       : {len(approved_df)}")

    if len(approved_df) == 0:
        print("\nNo approved rows found. Nothing to import. Exiting.")
        sys.exit(0)

    # ── 4. Make sure the tables exist ─────────────────────────────────────────
    Base.metadata.create_all(bind=engine)

    # ── 5. Open a database session and insert rows ────────────────────────────
    db = SessionLocal()
    inserted = 0
    skipped  = 0
    errors   = []

    print(f"\nImporting tasks...")

    for i, row in approved_df.iterrows():
        question_id = clean(row.get("question_id"))

        if not question_id:
            print(f"  Row {i}: skipped — empty question_id")
            skipped += 1
            continue

        # ── Skip if already exists (safe to re-run) ───────────────────────────
        exists = db.query(BenchmarkTask).filter_by(question_id=question_id).first()
        if exists:
            skipped += 1
            continue

        # ── Build the task object ─────────────────────────────────────────────
        try:
            task = BenchmarkTask(
                # ── Identity ──────────────────────────────────────────────────
                question_id = question_id,

                # ── Core question fields ──────────────────────────────────────
                prompt      = clean(row.get("prompt")),
                answer_type = clean(row.get("answer_type")),
                task_type   = clean(row.get("task_type")),
                task_format = clean(row.get("task_format")),
                gold_answer = clean(row.get("gold_answer")),

                # Options are stored as plain text in the Excel
                # (e.g. "A) RICHTIG | B) FALSCH")
                # We keep them as-is. The benchmark script reads them
                # as strings and parses them internally.
                options              = clean(row.get("options")),
                grading_criteria     = clean(row.get("grading_criteria")),
                numeric_tolerance    = clean_float(row.get("numeric_tolerance")),
                acceptable_variants  = clean(row.get("acceptable_variants")),

                # ── Context and attachments ───────────────────────────────────
                context        = clean(row.get("context")),
                attached_files = clean(row.get("attached_files")),

                # ── Regulatory and domain metadata ────────────────────────────
                regulatory_framework       = clean(row.get("regulatory_framework")),
                applicable_regulatory_year = clean_int(row.get("applicable_regulatory_year")),
                category                   = clean(row.get("category")),
                subcategory                = clean(row.get("subcategory")),
                skills                     = clean(row.get("skills")),
                education_level            = clean(row.get("education_level")),
                notes                      = clean(row.get("notes")),

                # ── Provenance ────────────────────────────────────────────────
                # The original source text from the Excel (e.g. "WiFi Prüfung...")
                # is stored in notes. The source field marks this as original data.
                source = "original_dataset",

                # submitted_by is null — these are not user contributions
                submitted_by = None,

                # ── Review status ─────────────────────────────────────────────
                # All original tasks are public immediately — no review needed.
                is_public         = True,
                validation_status = "approved",
                validated_by      = clean(row.get("validated_by")),

                # ── Timestamps ────────────────────────────────────────────────
                created_at = datetime.utcnow(),

                # ── No uploaded files for original tasks ──────────────────────
                pdf_path   = None,
                excel_path = None,
            )

            db.add(task)
            inserted += 1

            # Commit every 50 rows so progress is saved incrementally
            if inserted % 50 == 0:
                db.commit()
                print(f"  {inserted} tasks inserted so far...")

        except Exception as e:
            errors.append(f"Row {i} (question_id={question_id}): {e}")
            db.rollback()

    # ── 6. Final commit ───────────────────────────────────────────────────────
    try:
        db.commit()
    except Exception as e:
        print(f"\nERROR during final commit: {e}")
        db.rollback()
    finally:
        db.close()

    # ── 7. Summary ────────────────────────────────────────────────────────────
    print(f"\n{'─' * 50}")
    print(f"Import complete.")
    print(f"  Inserted : {inserted}")
    print(f"  Skipped  : {skipped}  (already in database or empty question_id)")
    print(f"  Errors   : {len(errors)}")

    if errors:
        print(f"\nErrors encountered:")
        for err in errors:
            print(f"  {err}")

    print(f"\nVerify in your database viewer:")
    print(f"  SELECT COUNT(*) FROM benchmark_tasks WHERE is_public = TRUE;")
    print(f"  Expected: {inserted}")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Import approved tasks from the ground-truth Excel into the database."
    )
    parser.add_argument(
        "--excel",
        default=DEFAULT_EXCEL_PATH,
        help=f"Path to the Excel file. Default: {DEFAULT_EXCEL_PATH}",
    )
    args = parser.parse_args()
    import_tasks(args.excel)
