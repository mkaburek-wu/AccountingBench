# Ground-truth sources — never attach these to a benchmark task

Both files in this folder would leak the answer if a model ever saw them. They are
kept out of `../attachments/` on purpose.

`resolve_attached_files()` in `backend/batch_utils.py` falls back to a **recursive
`os.walk` of the uploads tree by basename**, so a bare filename in an
`attached_files` cell can resolve to a file nobody intended to attach. Keeping these
two out of the attachment folder — and never naming them in a sheet — is what
prevents that.

| File | What it is | Why it must not be attached |
|---|---|---|
| `Email_Praxisfälle für LLM_Accounting Bench.pdf` | E-mail thread Mailis Klaus (KPMG Austria, Department of Professional Practice — Accounting) ↔ Manuel Kaburek, 22./23.09.2026 | Contains **the authoritative ground truth**: her closing assessment that no party controls the Paul Schwarz GmbH & Co. KG, and why. This is the source the `gold_answer` fields are built from. Also confidential KPMG correspondence. |
| `Test Beherrschung IFRS 10.docx` | Mailis Klaus's own chat transcript with GPT-5.6 Think Deeper (via Copilot) | **A model output, not ground truth.** Grading against it would score our models against another model's answer. It also reaches nearly the correct conclusion, so it is answer-leaking as well. |

## What the models actually receive

Only the eight derived PDFs in `../attachments/`, produced by
`backend/prepare_kpmg_attachments.py` from the two model-facing sources that remain
in the parent folder:

- `Gesellschaftsvertrag Beispiel 1.docx` — the anonymised partnership agreement
- `K4414-2025_geschwärzt_OCR-2.pdf` — Anlagen 1–3

`prepare_kpmg_attachments.py` asserts on every run that no string from the files in
this folder appears in any generated attachment (`CONTAMINATION_STRINGS`).

## Provenance note

Mailis Klaus asked for the models' *unaided* first assessment — she deliberately
withheld technical hints, and noted that arriving at a defensible answer normally
requires either several expert-guided iterations or access to KPMG's internal
*Insights* accounting manual, which is not public and is unlikely to be in any
model's training data. That is the point of the benchmark case: it measures how far
the models get without that support.
