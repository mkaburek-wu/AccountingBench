# AccountingBench — Claude Code Instructions

This file gives Claude context about the AccountingBench project when working in this repository.

---

## Project Overview

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

# Run migrations
python -m alembic upgrade head

# Start backend
python -m uvicorn backend.main:app --reload --port 8000
```

`.env` must be at the project root (not inside `backend/`). SQLite path needs 4 slashes on macOS:
```
DATABASE_URL=sqlite:////Users/yourname/Documents/AccountingBench/backend/accountingbench.db
```

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

---

## Frontend Rules

- **All CSS** → `public/styles.css`. No inline styles in HTML.
- **All data/numbers** → `public/results.js`. No hardcoded values in HTML.
- **All render logic** → `public/data.js`. HTML only has empty containers with IDs.
- Script load order in HTML: `results.js` → `data.js` → `main.js`
- No build step — files are served directly. Test with VS Code Live Server on port 5500.

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

# rerun_model.py — run new model on existing DB tasks
python -m backend.rerun_model --models "ModelName" --dry-run
python -m backend.rerun_model --models "ModelName" --limit 1 --sequential
python -m backend.rerun_model --models "ModelName" --max-workers 15
python -m backend.rerun_model --models "ModelA,ModelB" --max-workers 4

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
