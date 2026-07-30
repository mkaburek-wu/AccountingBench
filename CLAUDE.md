# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

# AccountingBench — Claude Code Instructions

AccountingBench is an academic LLM benchmarking platform evaluating AI models on accounting tasks (Tax, Financial Accounting, Management Accounting). Built at WU Vienna by the Financial Accounting & Auditing Group and the Board Service Center.

**Two components:**
- `public/` — static HTML/CSS/JS website (leaderboard, dashboard, methodology, about)
- `backend/` — FastAPI Python server (submission portal, benchmark pipeline, DB)

---

## Architecture

- **Backend:** FastAPI + SQLAlchemy + SQLite (local) / PostgreSQL (production)
- **Auth:** Clerk JWT tokens with domain restriction (`allowed_domains` table)
- **Pipeline:** `backend/processing/pipeline.py` — parallel model execution via `ThreadPoolExecutor`
- **Frontend:** Vanilla HTML/CSS/JS — no build step, no framework

---

## Critical Files

### Data layer (edit these to update results)
- `public/results.js` — **single source of truth** for all benchmark scores, model metadata, dataset composition. Never edit numbers directly in HTML.
- `public/data.js` — derived data + DOM render functions. Only edit to change layout or add new visualisations.
- `public/styles.css` — all CSS lives here. Never add inline styles to HTML files.

### Backend scripts
- `backend/batch_run.py` — imports tasks from Excel and runs full pipeline on all models
- `backend/rerun_model.py` — runs new model(s) on existing DB tasks (no Excel needed)
- `backend/batch_utils.py` — shared helpers imported by both batch scripts
- `backend/processing/pipeline.py` — the real benchmark pipeline (do not break this)

---

## How to Add a New Model

1. Add entry to `MODEL_REGISTRY_JSON` in `.env`
2. Add model name to `OPENAI_MODEL_LIST` in `.env`
3. Run `python -m backend.rerun_model --models "model-name" --dry-run` to verify
4. Run `python -m backend.rerun_model --models "model-name" --limit 1 --sequential` to test
5. Run full rerun: `python -m backend.rerun_model --models "model-name" --max-workers 15`
6. Add model to `BENCHMARK_RESULTS` in `public/results.js` with all score fields

---

## How to Update Scores (Frontend)

Edit `public/results.js` only. Everything else updates automatically:
- Ticker, leaderboard, holistic matrix, cost table, token bars, all charts
- Sort by overall score descending in the array

Each model needs these fields:
```
overall, tax, financial, management          ← category scores
interpLaw, calculation, journal              ← task type scores
multiChoice, openText, singleChoice, journalEntry  ← answer type scores
austrianTax, mixedAcc, ugb, ifrs             ← regulatory framework scores
eduProf, eduMaster, eduVoc                   ← education level scores
byEdu: { prof: {...}, master: {...}, voc: {...} }  ← full breakdown by edu level
n, priceIn, priceOut, cost, tokTask, speed   ← efficiency
calib: [{x, y, n}]                           ← confidence calibration
```

---

## Environment Setup

Always run commands from the project root `AccountingBench/`:

```bash
# Install dependencies
python -m pip install fastapi uvicorn sqlalchemy alembic python-dotenv pyjwt cryptography httpx anthropic openai pandas openpyxl pymupdf python-multipart stripe requests

# Run migrations (alembic.ini lives in backend/, not the project root)
python -m alembic -c backend/alembic.ini upgrade head

# Start backend
python -m uvicorn backend.main:app --reload --port 8000
```

`.env` must be at the project root (not inside `backend/`). SQLite path needs 4 slashes on macOS:
```
DATABASE_URL=sqlite:////Users/yourname/Documents/AccountingBench/backend/accountingbench.db
```

Set `DEBUG_PIPELINE=true` in `.env` to enable DEBUG-level logging of full prompts and model responses — essential for diagnosing pipeline scoring issues.

---

## Database Connection Pool

SQLite pool is configured in `backend/database.py`:
- `pool_size=20`, `max_overflow=40` → max 60 connections
- Safe parallelism: `floor(50 / num_models)` workers
- 13 models → `--max-workers 4` | 3 models → `--max-workers 15`

---

## Pipeline Notes

- All models run in parallel via `ThreadPoolExecutor` — each gets its own DB session
- Per-model timeout configured via `"timeout"` key in `MODEL_REGISTRY_JSON` (default: 240s)
- Kimi-K2.6 needs `"timeout": 600` — it is slow
- `OPENAI_API_KEY` must be set (can be `not-used`) even if all models use `MODEL_REGISTRY_JSON`
- Never change `run_pipeline()` signature — it is called from both web API and batch scripts
- PDF extraction uses PyMuPDF (`fitz`), not `pypdf`. Scanned image PDFs (no text layer) raise a `PDF_NO_TEXT` error, which the pipeline records as `ERROR:{model}` — do not reintroduce `pypdf`

**Constants in `pipeline.py` — must stay fixed across all runs for score comparability:**

| Constant | Value |
|---|---|
| `JUDGE_MODEL` | `"gpt-5-mini"` |
| `N_TRIALS` | `3` |
| `SYSTEM_PROMPT_VERSION` | `"v3_types"` |
| `DATASET_VERSION` | `"v3"` |

---

## Frontend Rules

- **All CSS** → `public/styles.css`. No inline styles in HTML.
- **All data/numbers** → `public/results.js`. No hardcoded values in HTML.
- **All render logic** → `public/data.js`. HTML only has empty containers with IDs.
- Script load order in HTML: `results.js` → `data.js` → `main.js`
- No build step — files are served directly. Test with VS Code Live Server on port 5500.

**HTML pages:**

| File | Purpose |
|---|---|
| `index.html` | Overview: scrolling ticker, hero section, mini leaderboard |
| `leaderboard.html` | Full sortable leaderboard + radar/bar charts |
| `dashboard.html` | Cost/speed scatter, token bars, calibration chart, KPI cards |
| `methodology.html` | Tabbed benchmark methodology documentation |
| `about.html` | Team and affiliation cards |
| `privacy.html` | Privacy policy |

---

## Key IDs in index.html

| ID | Rendered by |
|---|---|
| `ticker-inner` | `renderTicker()` |
| `overview-leaderboard` | `renderOverviewLeaderboard()` |
| `hm-thead` / `hm-tbody` | `renderHolisticMatrix(eduKey)` |
| `hm-caption` | `renderHolisticMatrix(eduKey)` |

---

## Batch Script Reference

```bash
# batch_run.py — import from Excel + run all models
python -m backend.batch_run --file backend/tasks.xlsx --approved --skip-existing
python -m backend.batch_run --file backend/tasks.xlsx --approved --max-workers 4
python -m backend.batch_run --file backend/tasks.xlsx --dry-run
python -m backend.batch_run --file backend/tasks.xlsx --sheet "Questions"  # default sheet name

# rerun_model.py — run new model on existing DB tasks
python -m backend.rerun_model --models "ModelName" --dry-run
python -m backend.rerun_model --models "ModelName" --limit 1 --sequential
python -m backend.rerun_model --models "ModelName" --max-workers 15
python -m backend.rerun_model --models "ModelA,ModelB" --max-workers 4
python -m backend.rerun_model --models "ModelName" --category "Tax"
python -m backend.rerun_model --models "ModelName" --task-type "calculation"
python -m backend.rerun_model --models "ModelName" --question-ids "q_0001,q_0042"
python -m backend.rerun_model --models "ModelName" --task-ids "19,42,100:110"

# inspect_db.py — print task fields + all runs/outputs for a given task (default: task 19)
python -m backend.inspect_db [task_id]

# reset_db.py — wipe all tasks/submissions (dev only)
python reset_db.py
```

---

## Team

- Ewald Aschauer — Head of Financial Accounting & Auditing Group, WU Vienna
- Alexander Hofer — University Assistant (Post-Doc)
- Markus Isack — University Assistant (Post-Doc)
- Manuel Kaburek — University Assistant (Prae-Doc)
- Daniel Höllmüller — Research Assistant