"""Offline verification of the KPMG IFRS 10 ground-truth sheet.

Reconstructs the exact prompt each model would receive, using the real pipeline
functions, and checks the sheet against what batch_run.py requires. Read-only:

  * no model API calls -- only resolve_attached_documents_text(), which for local
    absolute paths short-circuits to a plain file read (pipeline.py:515-521)
  * no database writes -- nothing is imported
  * batch_run --dry-run is deliberately NOT used at this stage, because it probes
    the model endpoints, which is a live call

Run from the project root:

    python -m backend.verify_kpmg_sheet

Exits non-zero if any check fails.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from backend.processing.pipeline import resolve_attached_documents_text

BASE = Path(__file__).resolve().parent / "uploads" / "Use_cases" / "KPMG"
SHEET_PATH = BASE / "tasks_kpmg_ifrs10.xlsx"
QUARANTINE = BASE / "_ground_truth_do_not_attach"

ATTACHMENTS_MAX_CHARS = 12_000
EXPECTED_DOCS = 8
EXPECTED_ROWS = 8

# The all-in-one row and the narrow rows it is composed from.
MERGED_ID = "20260924_0008"
MERGED_PART_IDS = [
    "20260924_0001", "20260924_0002", "20260924_0003",
    "20260924_0004", "20260924_0005", "20260924_0006",
]

REQUIRED_COLUMNS = [
    "question_id", "task_type", "prompt", "answer_type", "gold_answer",
    "regulatory_framework", "category", "education_level",
]
VALID_ANSWER_TYPES = {
    "single_choice", "multi_choice", "open_text", "open_numeric", "journal_entry",
}

# Each link in the control analysis must survive into the prompt.
DECISIVE = [
    "Letztentscheidungsrecht",
    "Investitionsentscheidungen innerhalb der bestehenden Budgetplanung",
    "625.000,00 EUR",
    "208.334,00 EUR",
    "Je 1,- EUR des Kapitalkontos",
    "Mehrheit von 2/3 der Stimmen der anwesenden",
    "Zustimmung zu zustimmungspflichtigen",
    "zweite Gesellschafterversammlung",
    "Festlegung des Jahresbudgets",
]

# Nothing from the ground-truth sources may reach a model.
CONTAMINATION = [
    "mklaus@kpmg.at",
    "Kaburek",
    "Im Ergebnis beherrscht keine Partei",
    "Think Deeper",
    "Praxisfälle",
]


def check(label: str, ok: bool, detail: str = "") -> bool:
    print(f"  [{'x' if ok else ' '}] {label}{(' - ' + detail) if detail and not ok else ''}")
    return ok


def main() -> int:
    if not SHEET_PATH.exists():
        print(f"ERROR: {SHEET_PATH} not found. Run build_kpmg_tasks_sheet first.")
        return 1

    frame = pd.read_excel(SHEET_PATH, sheet_name="Questions")
    failures: list[str] = []

    def fail_unless(label: str, ok: bool, detail: str = "") -> None:
        if not check(label, ok, detail):
            failures.append(f"{label}{(': ' + detail) if detail else ''}")

    # ── sheet structure ───────────────────────────────────────────────────────
    print("\nSheet structure")
    fail_unless(f"{EXPECTED_ROWS} rows", len(frame) == EXPECTED_ROWS, f"found {len(frame)}")
    missing = [c for c in REQUIRED_COLUMNS if c not in frame.columns]
    fail_unless("all required columns present", not missing, f"missing {missing}")
    fail_unless(
        "question_id unique",
        frame["question_id"].is_unique,
        "duplicates present",
    )
    fail_unless("attached_files column present", "attached_files" in frame.columns)

    bad_types = sorted(set(frame["answer_type"]) - VALID_ANSWER_TYPES)
    fail_unless("answer_type values valid", not bad_types, f"unknown {bad_types}")

    open_rows = frame[frame["answer_type"].isin({"open_text", "open_numeric", "journal_entry"})]
    no_criteria = open_rows[open_rows["grading_criteria"].isna()]["question_id"].tolist()
    fail_unless(
        "grading_criteria set on every judged row",
        not no_criteria,
        f"missing for {no_criteria}",
    )

    empty_gold = frame[frame["gold_answer"].isna()]["question_id"].tolist()
    fail_unless("gold_answer set on every row", not empty_gold, f"missing for {empty_gold}")

    fail_unless(
        "all rows share one attached_files value",
        frame["attached_files"].nunique() == 1,
    )
    fail_unless(
        "validation_status is pending (not yet confirmed by KPMG)",
        set(frame["validation_status"].dropna()) <= {"pending"},
    )

    # ── the prompt a model would actually receive ─────────────────────────────
    print("\nAttachment resolution (via the real pipeline function)")
    attached = frame["attached_files"].iloc[0]
    doc_text = resolve_attached_documents_text(attached)

    doc_markers = [f"[DOKUMENT {i}]" for i in range(1, EXPECTED_DOCS + 1)]
    present = [m for m in doc_markers if m in doc_text]
    fail_unless(
        f"all {EXPECTED_DOCS} documents resolved",
        len(present) == EXPECTED_DOCS,
        f"found {len(present)}",
    )
    fail_unless(
        "no document was truncated",
        "[... gekürzt ...]" not in doc_text,
        "a '[... gekürzt ...]' marker is present",
    )
    fail_unless(
        f"no [DOKUMENT {EXPECTED_DOCS + 1}] (unexpected extra attachment)",
        f"[DOKUMENT {EXPECTED_DOCS + 1}]" not in doc_text,
    )

    print("\nDecisive content reaches the model")
    for needle in DECISIVE:
        fail_unless(needle, needle in doc_text)

    print("\nNo contamination from the ground-truth sources")
    for needle in CONTAMINATION:
        fail_unless(f"absent: {needle!r}", needle not in doc_text)
    quarantined = sorted(p.name for p in QUARANTINE.iterdir() if p.is_file())
    leaked = [n for n in quarantined if n != "README.md" and n in attached]
    fail_unless(
        "no quarantined file named in attached_files",
        not leaked,
        f"leaked {leaked}",
    )

    # ── the merged row must really be the six narrow rows ─────────────────────
    # 20260924_0008 is only comparable with its parts if it asks exactly the same
    # questions and expects exactly the same content. It is composed from those rows
    # in build_kpmg_tasks_sheet.py; this re-checks the result in the written sheet.
    print("\nMerged row 20260924_0008 contains its six parts verbatim")
    merged = frame[frame["question_id"] == MERGED_ID]
    fail_unless(f"{MERGED_ID} present", len(merged) == 1)
    if len(merged) == 1:
        merged_prompt = str(merged["prompt"].iloc[0])
        merged_gold = str(merged["gold_answer"].iloc[0])
        merged_criteria = str(merged["grading_criteria"].iloc[0])

        for qid in MERGED_PART_IDS:
            part = frame[frame["question_id"] == qid]
            if len(part) != 1:
                failures.append(f"part row {qid} missing")
                continue
            # The narrow prompt is FRAMING + "FRAGESTELLUNG:\n" + the question, and
            # only the question text is carried into the merged prompt.
            question = str(part["prompt"].iloc[0]).split("FRAGESTELLUNG:\n", 1)[-1].strip()
            fail_unless(f"{qid} question text carried over", question in merged_prompt)
            fail_unless(
                f"{qid} gold answer carried over",
                str(part["gold_answer"].iloc[0]).strip() in merged_gold,
            )
            fail_unless(
                f"{qid} grading criteria carried over",
                str(part["grading_criteria"].iloc[0]).strip() in merged_criteria,
            )

        fail_unless(
            "rubric instructs the judge to average the six parts",
            "Durchschnitt der sechs Teilnoten" in merged_criteria,
        )
        fail_unless(
            "rubric scores an unanswered part as 0",
            "mit 0 zu" in merged_criteria,
        )

    # ── size report ───────────────────────────────────────────────────────────
    print("\nPrompt size per row (context is empty, so this is attachments + prompt)")
    print(f"  {'question_id':16s} {'prompt':>8s} {'documents':>10s} {'total':>8s}  ~tokens")
    for _, row in frame.iterrows():
        total = len(str(row["prompt"])) + len(doc_text)
        print(
            f"  {row['question_id']:16s} {len(str(row['prompt'])):8d} {len(doc_text):10d} "
            f"{total:8d}  ~{total // 4:,}"
        )

    print()
    if failures:
        print(f"FAILED - {len(failures)} check(s):")
        for item in failures:
            print(f"  - {item}")
        return 1

    print("All checks passed. The sheet is ready for KPMG review.")
    print("Nothing has been imported and no model has been run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
