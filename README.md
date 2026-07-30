# AccountingBench - Developer Documentation

A Structured Benchmark for Systematic Evaluation of Large Language Models in Accounting Education and Professional Tasks

Vienna University of Economics and Business (WU Vienna)

Keywords: Artificial Intelligence, LLM, Benchmarking, Accounting, Accounting and Information Systems



---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [File Structure](#2-file-structure)
3. [Database Schema](#3-database-schema)
4. [Authentication](#4-authentication)
5. [Backend API Endpoints](#5-backend-api-endpoints)
6. [Submission Pipeline](#6-submission-pipeline)
7. [Stripe Payment Flow](#7-stripe-payment-flow)
8. [Batch Runner (`batch_run.py`)](#8-batch-runner-batch_runpy)
9. [Model Re-run (`rerun_model.py`)](#9-model-re-run-rerun_modelpy) — incl. §9.8 pre-computed importer, §9.9 maintenance scripts, §9.10 per-task model scoping
10. [Frontend Pages](#10-frontend-pages)
11. [Environment Setup](#11-environment-setup)
12. [Clerk Configuration](#12-clerk-configuration)
13. [Remaining Implementation](#13-remaining-implementation)
14. [Database Administration (SQL Reference)](#14-database-administration-sql-reference)

---

## 1. Project Overview

AccountingBench is an academic benchmarking platform that evaluates large language models (LLMs) on accounting knowledge tasks. The platform has two components:

- **Public site** — a static HTML website showing the live leaderboard, model scores, methodology, and about pages.
- **Submission portal** — a private authenticated area where authorised users contribute new benchmark tasks. Tasks are automatically evaluated against all fixed models, results are stored in the database, and approved tasks are averaged into the public leaderboard.

> **Research context:** This project extends AccountingBench (academic paper, WU Vienna 2026) with a web-based contribution pipeline so the benchmark dataset can be grown collaboratively by authorised institutional users.

---

### 1.1 Technology Stack

| Component | Technology |
|---|---|
| Backend API | FastAPI (Python) — runs on port 8000 |
| Database | SQLite (local dev) / PostgreSQL (Render production) |
| ORM & migrations | SQLAlchemy + Alembic |
| Authentication | Clerk (JWT tokens, email verification) |
| Domain restriction | Custom FastAPI middleware (replaces Clerk Allowlist premium) |
| Payments | Stripe Checkout (hosted payment page) |
| Frontend — public | Static HTML + CSS + vanilla JavaScript |
| Frontend — portal | Static HTML pages served via Python HTTP server (port 5500) |
| File storage | Local filesystem (`uploads/` folder) |
| Deployment target | Render.com (Phase 6 — planned) |

---

### 1.2 Current Implementation Status

| Feature | Status | Notes |
|---|---|---|
| Database schema + migrations | ✅ Done | 7 tables, Alembic migrations applied |
| 521 original tasks imported | ✅ Done | From `matrikelnummer_ground_truth_template.xlsx` |
| FastAPI server | ✅ Done | Endpoints, running locally |
| Clerk authentication | ✅ Done | JWT verification via local PEM key + JWKS fallback |
| Domain restriction | ✅ Done | Checked against `allowed_domains` table on every request |
| Sign-in page | ✅ Done | Custom form calling Clerk API directly |
| Register page | ✅ Done | Domain pre-check + GDPR consent checkbox |
| Landing page | ✅ Done | Shows user's submission history |
| Upload form | ✅ Done | All task fields, up to 3 PDF + 3 Excel files (20 MB each), GDPR consent |
| Results page | ✅ Done | Dedicated page, pulls from database, no re-run |
| Account page | ✅ Done | `account.html` — view profile + delete account |
| Privacy policy | ✅ Done | `public/privacy.html` — GDPR-compliant placeholder with all third-party services |
| Mobile navigation | ✅ Done | Bottom tab bar on all auth pages; safe-area-aware padding |
| Data protection UI | ✅ Done | Consent checkboxes, data-use notices, footer privacy links across all pages |
| Dummy pipeline | ✅ Done | Always returns 100%, saves to database |
| Real benchmark pipeline | ✅ Done | `pipeline.py` — parallel models, LLM judge, per-model timeouts |
| Batch import + runner | ✅ Done | `batch_run.py` — Excel → DB → pipeline, parallelism control |
| Model re-run script | ✅ Done | `rerun_model.py` — run new models on existing DB tasks, with task filters |
| Pre-computed results importer | ✅ Done | `import_precomputed_results.py` — imports already-scored tasks/outputs from an external run, no live API calls |
| Shared batch utilities | ✅ Done | `batch_utils.py` — shared helpers for batch scripts |
| Idempotent result writes | ✅ Done | `pipeline.py` upserts on `(task_id, model_name)`; DB-level UNIQUE constraint makes duplicates impossible (see §3.3) |
| Per-task model scoping | ✅ Done | `rerun_model.py` runs only the models a task is actually missing (see §9.10) |
| Maintenance scripts | ✅ Done | `dedup_outputs.py`, `backfill_sc_mc_scores.py`, `fix_broken_options.py` — one-off data repairs (see §9.9) |
| Results.js recompute script | ✅ Done | `recompute_results.py` — recomputes `public/results.js` scores from a benchmark_tasks/benchmark_outputs Excel export, with a diff gate against unintended models (see §10.3) |
| Data-quality dry-run gate | ✅ Done | `--dry-run` flags buried option markers, option-letter gaps, unwinnable golds, unparseable tolerances (see §8.3) |
| Database reset utility | ✅ Done | `reset_db.py` — wipes tasks/submissions safely |
| Public site fully dynamic | ✅ Done | All charts/tables driven from `results.js` + `data.js` |
| Stripe payments | ✅ Done | Full Checkout flow with payment confirmation and pipeline trigger |
| Admin panel | ✅ Done | `admin.html` — task review, user management, live stats, domain management |
| Rate limiting | ✅ Done | `slowapi` — per-IP limits on all endpoints; tighter limits on submit + payment |
| Live leaderboard | ⏳ Planned | Phase 5 |
| Deployment to Render | ⏳ Planned | Phase 6 |

---

## 2. File Structure

### 2.1 Complete Directory Tree

```
accountingbench/
├── .env                           ← Environment variables (never commit)
├── reset_db.py                    ← Utility: wipe all tasks/submissions from DB
│
├── public/                        ← Public static site (served as-is)
│   ├── index.html                 ← Overview / home page (fully dynamic)
│   ├── leaderboard.html           ← Public leaderboard
│   ├── dashboard.html             ← Analytics dashboard (fully dynamic)
│   ├── methodology.html           ← Methodology explanation
│   ├── about.html                 ← About the project (5 team members)
│   ├── privacy.html               ← Privacy policy (GDPR, third-party services)
│   ├── styles.css                 ← Global CSS — all styles centralised here
│   ├── main.js                    ← Public site JavaScript
│   ├── results.js                 ← Single source of truth for ALL benchmark data
│   ├── data.js                    ← Derived data + DOM render functions
│   └── img/                       ← Logos and images
│
├── auth-pages/                    ← Private authenticated pages
│   ├── config.js                  ← ⚙️  Single config file: API URL + Clerk keys (edit for deployment)
│   ├── auth-pages.js              ← Shared JS utilities; injects Clerk script dynamically
│   ├── sign-in.html / sign-in.js  ← Login page + logic
│   ├── register.html / register.js← Registration page + GDPR consent
│   ├── landing.html / landing.js  ← Submission history page + logic
│   ├── upload.html / upload.js    ← Task contribution form + Stripe polling (up to 3 PDF/Excel files)
│   ├── payment-success.html / payment-success.js ← Post-Stripe redirect: confirms payment + pipeline
│   ├── account.html / account.js  ← Account settings: view profile + delete account
│   ├── admin.html / admin.js      ← Admin panel: task review, users, stats, domains
│   └── results.html               ← Benchmark result viewer (JS inline → results.js)
│
└── backend/                       ← FastAPI Python server
    ├── main.py                    ← App entry point, all endpoints
    ├── auth.py                    ← Clerk JWT verification + domain check
    ├── config.py                  ← Shared constants sourced from .env (APP_VERSION, pricing)
    ├── database.py                ← SQLAlchemy engine + session factory
    ├── limiter.py                 ← slowapi Limiter singleton + rate-limit thresholds
    ├── models.py                  ← 7 database table definitions
    ├── submissions.py             ← POST /submissions/prepare endpoint (multi-file upload)
    ├── payments.py                ← POST /submissions/{id}/confirm-payment endpoint
    ├── users.py                   ← DELETE /users/me (account deletion — DB then Clerk)
    ├── admin.py                   ← Admin endpoints: stats, user management, task review
    ├── import_tasks.py            ← One-time Excel → database migration
    ├── batch_run.py               ← Batch import + pipeline runner (see §8)
    ├── rerun_model.py             ← Run new model(s) on existing DB tasks (see §9)
    ├── import_precomputed_results.py ← Import already-scored tasks/outputs from Excel, no API calls (see §9.8)
    ├── dedup_outputs.py           ← Maintenance: remove duplicate/orphaned run+output rows (see §9.9)
    ├── backfill_sc_mc_scores.py   ← Maintenance: recompute stale SC/MC scores (see §9.9)
    ├── fix_broken_options.py      ← Maintenance: re-parse options stuck as {"raw": ...} (see §9.9)
    ├── recompute_results.py       ← Recomputes public/results.js from a benchmark_tasks/benchmark_outputs Excel export (see §10.3)
    ├── batch_utils.py             ← Shared helpers for batch_run + rerun_model
    ├── processing/
    │   ├── pipeline.py            ← Real benchmark pipeline (parallel models)
    │   └── dummy_pipeline.py      ← Test pipeline (always returns 100%)
    ├── migrations/                ← Alembic migration files
    │   └── versions/              ← Auto-generated migration scripts
    ├── accountingbench.db         ← SQLite database (local dev only)
    ├── uploads/                   ← User-uploaded files
    │   └── {user_id}/{sub_id}/    ← Per-submission file storage
    ├── alembic.ini                ← Alembic configuration
    └── requirements.txt           ← Python dependencies
```

> ⚠️ **Important:** The `.env` file must never be committed to Git. It contains secret API keys. Add `.env` and `accountingbench.db` to your `.gitignore` file.

---

## 3. Database Schema

The database has 7 tables defined in `backend/models.py` using SQLAlchemy. Migrations are managed by Alembic.

### 3.1 Table Overview

| Table | Purpose |
|---|---|
| `users` | One row per registered user. Populated on first Clerk login. |
| `allowed_domains` | Email domains permitted to register (e.g. `wu.ac.at`). |
| `benchmark_tasks` | Every benchmark question — both the original 521 and user submissions. |
| `benchmark_runs` | One row per model per benchmark execution (run metadata). |
| `benchmark_outputs` | One row per model per task (answers, scores, evaluation method). |
| `submissions` | Tracks each user contribution from submission through to review. |
| `settings` | Single-row config table (pricing, currency). |

---

### 3.2 Key Table Details

#### `benchmark_tasks`

This table replaces the ground-truth Excel spreadsheet. Column names match the spreadsheet exactly so the Python benchmark script can consume rows without changes.

| Field | Description |
|---|---|
| `question_id` | Unique ID. Format: `usr_xxxxxx` for user submissions, `q_NNNN` for originals. |
| `source` | `"original_dataset"` for the 521 imported tasks, `"user_submitted"` for new contributions. |
| `is_public` | `False` by default. Set to `True` by admin when task is approved for the leaderboard. |
| `validation_status` | `"approved"` \| `"pending"` \| `"rejected"` \| `"awaiting_payment"` |
| `answer_type` | `single_choice` \| `multi_choice` \| `open_text` \| `open_numeric` \| `journal_entry` |
| `gold_answer` | The correct answer. Letter(s) for choice tasks, value for numeric, text for open. |
| `grading_criteria` | Rubric used by the LLM judge for open-text and journal-entry tasks. |

#### `benchmark_outputs`

Mirrors the Outputs sheet of `final_evaluation_template.xlsx` exactly. One row per model per task.

| Field | Description |
|---|---|
| `run_id` | Shared across all models in a single benchmark run. |
| `final_score_percent` | The score used for leaderboard calculations (0–100). |
| `evaluation_method` | `"sc_mc_formula"` for choice tasks, `"judge"` for open tasks, `"dummy"` during testing. |
| `model_answer_1/2/3` | Three independent trial answers from the model. |
| `final_answer` | Majority vote (choice) or consolidation call result (open). |

> **Note on imported rows:** `import_precomputed_results.py` copies whatever the source sheet contains. If an external run recorded a `final_answer` and confidences but not every individual trial text, `model_answer_2/3` land as `NULL`. This is impossible for rows the live pipeline wrote — it only reaches the output write after all three trials succeed (see the trial-integrity rule in §6.4) — so a populated `final_answer` alongside a `NULL` trial answer is a reliable marker of imported data.

### 3.3 Uniqueness constraint on results

`benchmark_outputs` and `benchmark_runs` both carry a **`UNIQUE (task_id, model_name)`** constraint (migration `a3f9c1d8e2b7`). One model can therefore hold exactly one result per task, enforced by the database rather than by convention.

This exists because a re-run used to *insert* a second row instead of replacing the first, leaving the same task/model pair with two different scores and silently skewing every aggregate. Two layers now prevent that:

1. `pipeline.py` **upserts** — it looks for an existing `(task_id, model_name)` row and updates it in place, inserting only when none exists. Re-running a model overwrites its previous result.
2. The constraint rejects a duplicate outright, so any future code path that tries to blind-insert fails loudly with an `IntegrityError` instead of corrupting the data quietly.

> ⚠️ Because a re-run **overwrites**, re-running a model that already has a result replaces its score. Use `--skip-existing` (or `rerun_model.py`, which skips completed work by default) when you want to preserve existing results.

#### `submissions`

Tracks each user contribution lifecycle.

| Status | Meaning |
|---|---|
| `pending` | Saved, Stripe session being created in background. |
| `processing` | Payment confirmed, benchmark pipeline is running. |
| `done` | Script finished, scores available in database. |
| `error` | Script encountered an error. |

Payment fields on the `submissions` table:

| Field | Description |
|---|---|
| `payment_status` | `"unpaid"` → `"paid"` after Stripe confirms payment. |
| `stripe_payment_id` | Stripe PaymentIntent ID (e.g. `pi_...`). Set on payment confirmation. |
| `price_charged` | Amount charged in smallest currency unit (e.g. cents). |
| `checkout_url` | Stripe Checkout Session URL. Set by background task ~1 second after form submission. Frontend polls until this appears, then redirects. |

---

## 4. Authentication

### 4.1 How It Works

Authentication uses Clerk — a third-party service that handles user accounts, passwords, and email verification. The backend never stores passwords.

1. User signs in via Clerk on `sign-in.html`. Clerk issues a signed JWT session token.
2. The frontend sends this token as a `Bearer` header on every API request.
3. `auth.py` verifies the JWT signature using Clerk's RSA public key.
4. After JWT verification, the email domain is checked against the `allowed_domains` table.
5. If both checks pass, the endpoint receives the Clerk user ID string.

---

### 4.2 Token Verification Strategy

`auth.py` uses a two-step strategy to work on restricted networks (e.g. university machines that block outbound internet):

**Step 1 — Local PEM key (primary)**
Verifies the JWT using the RSA public key stored in `.env` as `CLERK_PEM_PUBLIC_KEY`. Fast, no network call, works on restricted machines.

**Step 2 — JWKS fallback (automatic)**
If the local key fails (e.g. after Clerk key rotation), the code fetches Clerk's public keys from the JWKS endpoint. Requires internet access. Works automatically on Render in production.

---

### 4.3 Domain Restriction

Clerk's Allowlist feature (which restricts registration by email domain) requires a paid plan. Instead, domain restriction is implemented entirely in FastAPI:

**Frontend check (register.html)**
Before creating a Clerk account, the frontend calls `GET /auth/check-domain`. If the domain is not in the `allowed_domains` table, the user sees an error immediately and no Clerk account is created.

**Backend check (every request)**
Every protected endpoint calls `_check_domain()` inside `get_current_user()`. This is a second layer — even if someone bypasses the frontend check, the backend rejects them.

**Admin management**
Domains can be added and removed via the admin API endpoints (`GET`/`POST`/`DELETE /admin/domains`) or directly in the database.

---

### 4.4 FastAPI Dependencies

Three reusable dependencies are defined in `auth.py`:

```python
# Any signed-in user with an allowed domain
@app.get("/submissions/mine")
def my_submissions(user_id: str = Depends(get_current_user), db = Depends(get_db)):
    ...

# Admin only (email must match ADMIN_EMAIL in .env)
@app.post("/admin/tasks/{task_id}/approve")
def approve(task_id: int, admin_id: str = Depends(require_admin), db = Depends(get_db)):
    ...

# Public endpoint that optionally personalises for signed-in users
@app.get("/api/leaderboard")
def leaderboard(user_id: str | None = Depends(get_optional_user)):
    ...
```

---

## 5. Backend API Endpoints

The FastAPI server runs at `http://127.0.0.1:8000`. Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

### 5.1 Public Endpoints (no authentication required)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Health check — returns API status. |
| `GET` | `/health` | Detailed health check including database connection. |
| `GET` | `/api/leaderboard` | Returns current leaderboard data from database. |
| `GET` | `/auth/check-domain?domain=` | Checks if a domain is in the allowed list. Used by `register.html`. |

### 5.2 Protected Endpoints (require sign-in)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/me` | Returns the signed-in user's profile (id, email, first/last name). |
| `DELETE` | `/users/me` | Permanently deletes the account. Removes all DB records first, then calls the Clerk API. |
| `GET` | `/submissions/mine` | Returns the user's submission history for the landing page. |
| `GET` | `/submissions/{id}/status` | Returns submission status, `checkout_url`, and model scores when done. Polled by both `upload.html` and `results.html`. |
| `POST` | `/submissions/prepare` | Receives the upload form (up to 3 PDF + 3 Excel files), saves task + files, queues Stripe session creation as a background task. Returns immediately. |
| `POST` | `/submissions/{id}/confirm-payment` | Called by `payment-success.html` after Stripe redirects back. Verifies the Checkout Session with Stripe, marks submission as paid, triggers the benchmark pipeline. Idempotent — safe to call multiple times. |

### 5.3 Admin Endpoints (require `ADMIN_EMAIL`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/admin/tasks?status=pending` | Lists tasks pending review. Also accepts `approved`/`rejected`. |
| `POST` | `/admin/tasks/{id}/approve` | Approves a task — sets `is_public=True` so it appears in the leaderboard. |
| `POST` | `/admin/tasks/{id}/reject` | Rejects a task — stays private. |
| `GET` | `/admin/stats` | Returns KPI counts: pending/approved/rejected tasks, users, submissions today/week/total, revenue. |
| `GET` | `/admin/users` | Lists all users with submission counts. |
| `POST` | `/admin/users/{id}/deactivate` | Deactivates a user account (blocks API access). |
| `POST` | `/admin/users/{id}/activate` | Re-activates a user account. |
| `GET` | `/admin/domains` | Lists all allowed email domains. |
| `POST` | `/admin/domains` | Adds a new allowed domain. Body: `{"domain": "kpmg.com"}`. |
| `DELETE` | `/admin/domains/{id}` | Removes an allowed domain. |

---

## 6. Submission Pipeline

### 6.1 Full Flow (with Stripe)

When a user submits a task on `upload.html`, the following happens:

1. `upload.html` validates all required fields in the browser before sending.
2. `POST /submissions/prepare` receives the form data and files.
3. `submissions.py` validates fields server-side (enum values, conditional requirements, file types up to 20 MB).
4. A unique `question_id` is generated (format: `usr_xxxxxx`).
5. Uploaded files are saved to `uploads/{user_id}/{submission_id}/`.
6. A row is inserted into `benchmark_tasks` (`validation_status=awaiting_payment`).
7. A row is inserted into `submissions` (`payment_status=unpaid`).
8. **The endpoint returns immediately** — Stripe session creation is queued as a background task (avoids blocking the HTTP response).
9. `upload.html` shows a "Preparing Payment" spinner and polls `GET /submissions/{id}/status` every 500 ms.
10. In the background (~1 second), `_create_stripe_session()` calls Stripe and saves `checkout_url` to the submission row.
11. The polling loop finds `checkout_url` and redirects the browser to Stripe's hosted checkout page.
12. User completes payment on Stripe's page.
13. Stripe redirects to `payment-success.html?submission=N&stripe_session=cs_...`
14. `payment-success.html` calls `POST /submissions/{id}/confirm-payment` with the Stripe session ID.
15. The backend verifies the payment with Stripe, marks the submission as `paid`, moves the task to `pending`, and triggers the benchmark pipeline as a background task.
16. `payment-success.html` polls `GET /submissions/{id}/status` every 3 seconds.
17. When `status=done`, the browser navigates to `results.html?submission={id}`.
18. `results.html` shows the model scores from the database — **the pipeline never runs again**.

**Cancellation:** If the user clicks "Back" or "Cancel" on the Stripe checkout page, Stripe redirects to `upload.html?cancelled=1`, which shows a cancellation banner so the user can try submitting again.

---

### 6.2 Flow Without Stripe (development)

If `STRIPE_SECRET_KEY` is not set in `.env`, the flow skips payment entirely:

1. `POST /submissions/prepare` triggers the benchmark pipeline immediately as a background task.
2. `upload.html` polls status and redirects to `results.html` when `status=processing`.

---

### 6.3 Dummy Pipeline (Testing)

`backend/processing/dummy_pipeline.py` is used during development. It:

- Sets submission status to `"processing"`
- Waits 3 seconds to simulate runtime
- Inserts one `BenchmarkRun` + one `BenchmarkOutput` row for each model with `final_score_percent = 100.0`
- Sets submission status to `"done"`

> ✅ **Swapping to the real pipeline:** Change one import line in both `submissions.py` and `payments.py`:
> ```python
> # Testing (current):
> from backend.processing.dummy_pipeline import run_pipeline
>
> # Production (real script):
> from backend.processing.pipeline import run_pipeline
> ```
> Everything else stays the same.

---

### 6.4 Pipeline Architecture (`pipeline.py`)

The real benchmark pipeline in `backend/processing/pipeline.py`:

- Reads the task from `benchmark_tasks` by `submission.task_id`
- Extracts attached PDF/file content and injects it into the prompt
- Calls all models listed in `OPENAI_MODEL_LIST` in parallel via `ThreadPoolExecutor`
- Each model runs 3 independent trials, then a consolidation call, then a judge call
- Scoring: `single_choice`/`multi_choice` → SC/MC formula; `open_text`/`open_numeric`/`journal_entry` → LLM-as-judge
- Writes one `benchmark_outputs` row per model
- A submission is marked `done` **only when every model produces output** — any failure or skip sets `status = "error"` and raises `IncompleteRunError`, stopping the batch script cleanly

**Trial integrity rule:**

Each model runs 3 independent trials. If any trial requires a retry (due to a transient error), the model run is aborted immediately with a `RuntimeError`. This prevents benchmarking a model under degraded conditions — benchmark scores must come from clean, uninterrupted runs. Rerun the affected model once the API is stable.

**Judge enrichment:**

For open-ended tasks (`open_text`, `open_numeric`, `journal_entry`), the LLM judge receives three additional fields from the task record:

| Field | Used for | Effect |
|---|---|---|
| `grading_criteria` | `open_text`, `journal_entry` | Rubric shown to the judge as `BEWERTUNGSKRITERIEN` |
| `acceptable_variants` | all open types | Pipe-separated alternative valid answers shown as `AKZEPTABLE VARIANTEN` |
| `numeric_tol` | `open_numeric` only | Tolerance band — answers within ±N are fully correct |

These fields are read from `benchmark_tasks` and must be set before the pipeline runs. The dry-run field consistency check (see §8.3) flags tasks where required fields are missing.

> ⚠️ `numeric_tolerance` must be parsed with `parse_tolerance()`, never bare `float()`. The ground-truth sheets write tolerances as `"+/- 1"`, `"± 5"`, `"+/- 0,01"` — `float()` rejects all of those, and the old importer caught the `ValueError` and stored `None`, leaving the judge with no tolerance band while the sheet still looked populated. `--dry-run` now emits a `TOL` warning for any tolerance it cannot parse.

**Which models run:**

`run_pipeline()` resolves its model list in this order:

1. `pipeline.MODEL_LIST_OVERRIDE` — a `contextvars.ContextVar`. Set it to scope a *single* `run_pipeline()` call to specific models. Because `contextvars` are thread-local, each `ThreadPoolExecutor` worker gets its own value, so concurrent callers cannot clobber each other the way a shared `os.environ` write would. `rerun_model.py` uses this to run only a task's missing models (see §9.10).
2. `OPENAI_MODEL_LIST` env var — the normal path for `batch_run.py` and the web submission flow.
3. `ALL_MODELS` — the hardcoded fallback in `pipeline.py`. Every name here must exist in `MODEL_REGISTRY_JSON`, otherwise that model 404s, is skipped, and the run aborts with `IncompleteRunError`.

**Result writes are idempotent:** each model's `BenchmarkRun` and `BenchmarkOutput` row is written with an upsert keyed on `(task_id, model_name)` — see §3.3 for why, and for the overwrite caveat.

**Error handling:**

| Error type | Behaviour |
|---|---|
| Transient (429, 5xx, timeout, connection reset) | Retry once — 60s delay for 429, 5s for others |
| Any trial needs a retry | `RuntimeError` raised — model run aborted to preserve benchmark integrity |
| Not found (404) | Skip model, task marked incomplete → stop |
| PDF attachment yields no extractable text (scanned image PDF) | `TaskLevelError` raised → all model threads cancelled immediately → run stops |
| Attached file not found on disk | `TaskLevelError` raised → all model threads cancelled immediately → run stops |
| Any model fails or is skipped | `IncompleteRunError` raised → stop script after running tasks finish |
| Insufficient balance | Retry once after 30s; stop script if confirmed |

**Recovery after a stopped run** (no data is lost — resume in two steps):
```bash
# 1. Re-run tasks that were never started (not yet in DB)
python -m backend.batch_run --file backend\tasks.xlsx --approved --skip-existing

# 2. Fill in missing model outputs on any partially-failed task
python -m backend.rerun_model
```

> **Note:** `cleanup_failed.py` is only needed if you want to completely reset a task (e.g. the task data itself was wrong). For normal interrupted runs, the two-step resume above is sufficient.

### 6.5 Model Configuration

Models are configured via two `.env` variables:

```
OPENAI_MODEL_LIST=claude-opus-4-6,claude-sonnet-4-6,gpt-5.2,...
MODEL_REGISTRY_JSON={"model-name": {"api_type": "...", "base_url": "...", "api_key": "...", "timeout": 300}, ...}
```

**Supported `api_type` values:**

| `api_type` | Protocol | Used for |
|---|---|---|
| `openai_v1` | OpenAI Chat / Responses API | OpenAI, Cortecs, DeepSeek, Mistral, Kimi, Mercury |
| `alawyer` | Custom SSE (POST `/api/v1/completions`) | Alawyer Austrian legal AI |

**Optional keys per model entry:**

| Key | Type | Description |
|---|---|---|
| `timeout` | number | Per-model timeout in seconds (default: 240). Use 600+ for slow models like Kimi. |
| `model_id` | string | API model ID to send to the provider. Use when the registry key differs from the provider's model name (e.g. Cortecs model IDs use different casing). |
| `allowed_providers` | list | Restrict Cortecs routing to specific backend providers, e.g. `["amazon_ireland"]`. Useful to avoid providers that don't support certain parameters. |
| `no_temperature` | bool | If `true`, omits the `temperature` parameter from the API call. Required for newer Claude models (4.7+) where temperature is deprecated by Anthropic. |
| `extra_body` | object | Any additional fields to pass in the request body (merged at the top level). Useful for provider-specific parameters. |

**Example — Claude model on Cortecs routed to Amazon Bedrock:**

```json
"claude-opus-4-7": {
    "api_type": "openai_v1",
    "base_url": "https://api.cortecs.ai/v1",
    "api_key": "...",
    "model_id": "claude-opus4-7",
    "allowed_providers": ["amazon_ireland"],
    "no_temperature": true
}
```

**Example — slow model with extended timeout:**

```json
"Kimi-K2.6": {
    "api_type": "openai_v1",
    "base_url": "https://api.cortecs.ai/v1",
    "api_key": "...",
    "model_id": "kimi-k2.6",
    "timeout": 600
}
```

**`${ENV_VAR}` references in `api_key`:** Instead of hardcoding a key in `MODEL_REGISTRY_JSON`, you can reference an environment variable using the `${VAR_NAME}` syntax. The pipeline resolves it at runtime:

```json
"alawyer": {
    "api_type": "alawyer",
    "base_url": "https://app.alawyer.ai",
    "api_key": "${ALAWYER_API_KEY}",
    "timeout": 660
}
```

Then set `ALAWYER_API_KEY=your-key` separately in `.env`.

**Cortecs model IDs:** The Cortecs API uses its own model ID strings that differ from the display names. Always verify the exact ID via `GET https://api.cortecs.ai/v1/models` and set `model_id` accordingly. Use `allowed_providers` to pin routing to a specific backend (e.g. `amazon_ireland` instead of the default Google Vertex AI for Claude models).

**Alawyer-specific notes:**
- API rate limit is **10 requests per minute** — use `--max-workers 1` or `--max-workers 2` when running `rerun_model.py`
- Each call takes 1–10 minutes; `timeout` is set to 660s (11 minutes) by default
- Alawyer returns free-form legal text, not JSON. The pipeline extracts a structured answer via a secondary judge call. Scoring works best on `open_text` and `journal_entry` tasks; choice tasks will score 0
- Confidence is not available from the Alawyer API — `avg_model_confidence` will be `null`
- When Alawyer has no answer for a query it returns `{"error": {"message": "empty_answer"}}` — the pipeline treats this as an empty response (score 0) rather than a fatal error

---

## 7. Stripe Payment Flow

### 7.1 Overview

AccountingBench uses Stripe Checkout — Stripe's fully hosted payment page. The backend never handles raw card data.

**Flow summary:**
```
upload.html → /submissions/prepare → (background) Stripe Session created
    → poll /status → redirect to Stripe → payment
    → payment-success.html → /confirm-payment → pipeline → results.html
```

### 7.2 Required Stripe Keys

In the [Stripe Dashboard](https://dashboard.stripe.com) → Developers → API Keys:

| Key | Where to put it |
|---|---|
| Secret key (`sk_test_...` or `sk_live_...`) | `.env` → `STRIPE_SECRET_KEY` |
| Publishable key (`pk_test_...` or `pk_live_...`) | Not used server-side; for reference only |
| Webhook signing secret | `.env` → `STRIPE_WEBHOOK_SECRET` (optional — not used currently) |

### 7.3 `FRONTEND_URL` — Critical for Redirects

Stripe needs to know where to redirect the user after payment (success or cancel). This is set via `FRONTEND_URL` in `.env`.

```
FRONTEND_URL=http://127.0.0.1:5500
```

**Why this matters:**

When a user completes or cancels payment on Stripe's hosted checkout page, Stripe redirects their browser to URLs built from `FRONTEND_URL`:

- **Success:** `{FRONTEND_URL}/auth-pages/payment-success.html?submission=N&stripe_session=cs_...`
- **Cancel:** `{FRONTEND_URL}/auth-pages/upload.html?cancelled=1`

If `FRONTEND_URL` is wrong, the user lands on the wrong page (or nowhere) after payment.

**Local development:**

```
FRONTEND_URL=http://127.0.0.1:5500
```

> ⚠️ Use `127.0.0.1`, not `localhost`. On Windows, `localhost` resolves to IPv6 (`::1`) while Clerk sessions are bound to `127.0.0.1`. Using `localhost` here causes the browser to land on a different origin after the Stripe redirect, which makes Clerk think the user is not signed in and sends them to the sign-in page.

**Production (Render):**

```
FRONTEND_URL=https://your-site.onrender.com
```

Replace `your-site` with the actual subdomain Render assigns to your static site. This is the URL where `auth-pages/` is publicly accessible. When you deploy, this is the only value you need to change for Stripe redirects to work on production.

### 7.4 Stripe Price Configuration

The price per submission is stored in the `settings` table (not hardcoded). It can be changed without redeploying:

```sql
-- View current price
SELECT price_per_submission, currency FROM settings WHERE id = 1;

-- Change to €30 (amount is always in smallest currency unit: cents)
UPDATE settings SET price_per_submission = 3000, currency = 'eur' WHERE id = 1;
```

Default: 5000 cents = €50.

### 7.5 Security: Session Substitution Prevention

`payments.py` checks that the Stripe Checkout Session's `metadata.submission_id` matches the URL parameter. This prevents a user from paying for one submission and then reusing that payment to confirm a different (more expensive or someone else's) submission.

### 7.6 Idempotency

`POST /submissions/{id}/confirm-payment` is idempotent. If the user refreshes `payment-success.html` after payment, the endpoint returns `{"ok": true, "already_paid": true}` immediately without re-contacting Stripe or re-triggering the pipeline.

### 7.7 Switching from Dummy to Real Pipeline

The `confirm-payment` endpoint currently uses the dummy pipeline for testing:

```python
# backend/payments.py — near the bottom
from backend.processing.dummy_pipeline import run_pipeline   # ← testing
# from backend.processing.pipeline import run_pipeline       # ← production
```

Also update the same import in `submissions.py` (used for the no-Stripe dev path).

---

## 8. Batch Runner (`batch_run.py`)

`backend/batch_run.py` is a command-line tool for importing tasks from an Excel file and running the full benchmark pipeline on them. It is the primary tool for large-scale data ingestion during development and evaluation.

### 8.1 Basic Usage

Always run from the project root (`accountingbench/`):

```bash
python -m backend.batch_run --file backend\tasks.xlsx [options]
```

### 8.2 All Flags

| Flag | Default | Description |
|---|---|---|
| `--file` | *(required)* | Path to Excel file (must have a `Questions` sheet) |
| `--sheet` | `Questions` | Sheet name to read from |
| `--approved` | off | Mark tasks as `validation_status=approved` and `is_public=True` immediately |
| `--skip-existing` | off | Skip tasks whose `question_id` is already in the database |
| `--sequential` | off | Run tasks one at a time instead of in parallel. `--max-workers 1` is equivalent. |
| `--max-workers` | `4` | Maximum number of tasks to run in parallel. Setting this to `1` behaves identically to `--sequential`. |
| `--limit` | off | Only process the first N tasks (useful for testing) |
| `--dry-run` | off | Full pre-flight validation — no DB writes, no API calls (see §8.3) |
| `--uploads-dir` | `backend/uploads` | Folder to search for attached files referenced in the Excel |
| `--user` | `batch_admin` | User ID to attribute submissions to |

### 8.3 Common Commands

**`--dry-run` runs these checks in order (no DB writes, no API calls):**

| # | Check | What it catches |
|---|---|---|
| 1 | Required fields | Rows with empty `question_id`, `prompt`, `answer_type`, `gold_answer`, `regulatory_framework`, `category`, or `education_level` |
| 2 | Duplicate IDs | Same `question_id` appearing more than once in the sheet |
| 3 | Skip-existing preview | How many tasks already exist in the DB vs how many are new *(only shown with `--skip-existing`)* |
| 4 | Field consistency | See the warning-code table below — answer types, rubrics, tolerances, and option/gold integrity |
| 5 | Attached files + PDF readability | Which referenced files can / cannot be found under `--uploads-dir`; warns if any PDF has no extractable text (scanned image — would raise `PDF_NO_TEXT` at runtime) |
| 6 | API endpoints | Whether each model in `OPENAI_MODEL_LIST` is reachable and authenticated |

**Field consistency warning codes** (emitted by `check_field_consistency()` in `batch_utils.py`, used by both `batch_run.py` and `rerun_model.py`):

| Code | Meaning | Why it matters |
|---|---|---|
| `TYPE` | `answer_type` is not one of the five recognised values | Task cannot be scored — a blank trailing Excel row imports as a live, public, unscoreable task |
| `MISS` | `grading_criteria` empty on `open_text`/`journal_entry`, or `numeric_tolerance` unset on `open_numeric` | Judge runs with no rubric / no tolerance band |
| `TOL` | `numeric_tolerance` is present but unparseable | Stored as `NULL` — the sheet looks populated but the judge gets nothing |
| `OPTS` | options stuck as `{"raw": ...}`; **or** an option's text contains a buried `X)` marker; **or** the option letters have a gap (`A, B, D, E`) | A swallowed option means models see a malformed choice list, and the missing letter vanishes from the parsed set |
| `GOLD` | `gold_answer` uses `;` instead of `,`; **or** it cites an option letter that does not exist | Scoring silently returns 0, or **no model can ever reach full marks** |

> **Why detection instead of a smarter parser:** `parse_options()` only treats `X)` as a new option at the start of a line, which is what lets a second option on the same line get absorbed. Loosening that regex to split after any whitespace would wrongly split ordinary German legal citations (`§ 4 Abs 1 Z 2 lit b) EStG`, `gemäß lit a)`) across the whole corpus. Flagging the anomaly at dry-run time and fixing the source sheet is the safer trade.

```bash
# Full pre-flight check before a real run (always do this first)
python -m backend.batch_run --file backend\tasks.xlsx --dry-run

# Pre-flight check including skip-existing preview
python -m backend.batch_run --file backend\tasks.xlsx --dry-run --skip-existing

# Test on a single task before a full run
python -m backend.batch_run --file backend\tasks.xlsx --approved --limit 1 --sequential

# Import and run all tasks, mark as approved, skip already-imported ones
python -m backend.batch_run --file backend\tasks.xlsx --approved --skip-existing

# Run sequentially (safest, lowest DB load)
python -m backend.batch_run --file backend\tasks.xlsx --approved --sequential

# Control parallelism explicitly
python -m backend.batch_run --file backend\tasks.xlsx --approved --max-workers 4

# Resume an interrupted run (fix model config first, then):
python -m backend.batch_run --file backend\tasks.xlsx --approved --skip-existing  # tasks not yet in DB
python -m backend.rerun_model                                                      # missing model outputs
```

### 8.4 Parallelism and DB Connection Limits

The batch runner processes multiple tasks simultaneously. Each task runs all its models in parallel internally, so the total number of simultaneous DB connections is:

```
max_workers × number_of_models = simultaneous DB connections
```

The SQLite connection pool in `database.py` is configured with a maximum of **100 connections** (pool_size=20, max_overflow=80). Choose `--max-workers` accordingly:

| Models | Recommended max-workers | Connections used |
|---|---|---|
| 3 | 15 | 45 |
| 13 | 4 | 52 |

> ⚠️ Never pass `--max-workers` higher than these values or you will hit connection pool timeouts. Never run 500+ tasks fully in parallel — use `--max-workers` to throttle throughput.

### 8.5 Progress Logging

The script logs `[X/N]` counters on every line so you can track exactly which task is running:

```
────────────────────────────────────────────────────────────
  Task 3/20: 12008933_0003
────────────────────────────────────────────────────────────
[3/20]  ── Task: 12008933_0003 ──────────────────────────
[3/20]  [RUN] 12008933_0003 → submission 42 — starting pipeline...
[3/20]  [DONE] 12008933_0003 → submission 42 — pipeline complete.
```

In parallel mode the `[X/N]` prefix appears on every log line, making it possible to follow individual tasks even when output is interleaved.

### 8.6 Error Log File

Every run (both `batch_run.py` and `rerun_model.py`) automatically writes a timestamped error log to the `logs/` folder in the project root:

```
logs/batch_run_errors_20260615_161145.log
logs/rerun_model_errors_20260615_161145.log
```

Only `WARNING` and above is written to the file — `INFO` output stays in the terminal only. The log path is printed at the start of every run. Review this file after a run to see all model errors and warnings without scrolling through the full terminal output.

### 8.8 Debug Logging

To see the full prompt sent to each model and the raw response, enable DEBUG logging by adding this line after the logger setup in `batch_run.py`:

```python
logging.getLogger("backend.processing.pipeline").setLevel(logging.DEBUG)
```

This shows `[LLM→]` (prompt sent) and `[LLM←]` (raw response) lines for every model call. Remove or comment out this line to return to normal INFO logging.

### 8.9 Attached Files

If a task references a PDF, the script searches for it in this order:

1. URLs — passed through unchanged
2. Absolute paths — used as-is if the file exists
3. Relative path under `--uploads-dir`
4. Bare filename under `--uploads-dir`
5. Recursive search under `--uploads-dir`
6. Not found — warns and keeps the raw string

PDF content is extracted and injected into the prompt as `DOKUMENT-INHALT (extrahiert):` before the question text.

### 8.10 Resetting the Database

During development, use `reset_db.py` to wipe all tasks, submissions, runs and outputs:

```bash
python reset_db.py
```

The script asks for confirmation before deleting anything. It preserves `settings`, `allowed_domains`, and `users` tables untouched.

---

## 9. Model Re-run (`rerun_model.py`)

`backend/rerun_model.py` runs one or more models against all tasks already in the database. Use it when:
- Adding a **new model** to the benchmark (without re-importing from Excel)
- **Resuming an interrupted run** — it automatically detects which models are missing outputs for each task and only runs those, skipping everything already complete

### 9.1 Key Differences from `batch_run.py`

| | `batch_run.py` | `rerun_model.py` |
|---|---|---|
| Input | Excel file | DB directly (no file needed) |
| Task selection | All rows in Excel | All tasks in DB |
| Skip logic | Skips tasks already in DB | Skips tasks where model output already exists |
| Model selection | All models in `OPENAI_MODEL_LIST` | Only the models you specify |
| Use case | Initial import + full run | Add a new model to existing results |

### 9.2 All Flags

**Execution flags:**

| Flag | Default | Description |
|---|---|---|
| `--models` | *(from `.env`)* | Comma-separated model name(s) from `MODEL_REGISTRY_JSON`. If omitted, `OPENAI_MODEL_LIST` from `.env` is used. |
| `--max-workers` | `10` | Max parallel tasks. Rule of thumb: `floor(50 / num_models)` |
| `--sequential` | off | Run one task at a time |
| `--dry-run` | off | Print plan, probe all model API endpoints — no DB writes or API calls |
| `--limit` | off | Only process first N tasks (useful for testing) |
| `--user` | `batch_admin` | User ID for created submissions |

**Filter flags** (all optional, combinable, comma-separated for multiple values):

| Flag | Filters on | Valid values |
|---|---|---|
| `--category` | `category` | `Tax`, `Financial Accounting`, `Management Accounting` |
| `--task-type` | `task_type` | `interpretation_of_law`, `calculation`, `journal_entry` |
| `--answer-type` | `answer_type` | `single_choice`, `multi_choice`, `open_text`, `open_numeric`, `journal_entry` |
| `--education-level` | `education_level` | `Professional Examinations`, `University Master's`, `Secondary Vocational` |
| `--regulatory-framework` | `regulatory_framework` | `Austrian Tax Law`, `IFRS`, `National GAAP`, `Mixed Accounting Framework`, `Mixed: Accounting + Tax` |
| `--question-ids` | `question_id` | Exact IDs, prefixes, or ranges — see below |
| `--task-ids` | `id` (integer primary key) | Exact IDs or ranges — see below |

Filters are applied at the SQL query level before the skip-existing check, so they compose cleanly with `--limit` and `--dry-run`.

#### `--question-ids` syntax

Each comma-separated token can be one of three forms (mix freely):

| Token form | Example | Matches |
|---|---|---|
| Exact | `11908783_0028` | that single task |
| Prefix | `11908783` | all `11908783_*` tasks |
| Range | `11908783_0001:11908783_0050` | `_0001` through `_0050` inclusive (lexicographic) |

Multiple tokens are combined with OR logic:

```bash
--question-ids "11908783,12345678_0001:12345678_0010,99999999_0042"
```

#### `--task-ids` syntax

Filters on `BenchmarkTask.id`, the integer primary key (e.g. as printed by `backend/inspect_db.py`), not `question_id`. Each comma-separated token can be one of two forms (mix freely):

| Token form | Example | Matches |
|---|---|---|
| Exact | `19` | that single task |
| Range | `13:543` | ids `13` through `543` inclusive |

Multiple tokens are combined with OR logic:

```bash
--task-ids "19,13:543,1000:1199"
```

### 9.3 Common Commands

```bash
# Resume an interrupted run — fills in ALL missing model outputs across all tasks
python -m backend.rerun_model

# Step 1 — always dry-run first to see what would happen (no API calls, no DB writes)
python -m backend.rerun_model --models "Kimi-K2.6" --dry-run

# Step 2 — test on exactly 1 task to verify the pipeline works end-to-end
python -m backend.rerun_model --models "Kimi-K2.6" --limit 1 --sequential

# Step 3 — run on all tasks (choose max-workers based on model count)
python -m backend.rerun_model --models "Kimi-K2.6" --max-workers 15

# Multiple models at once
python -m backend.rerun_model --models "Kimi-K2.6,gpt-5.5" --max-workers 4

# Safest option for large datasets
python -m backend.rerun_model --models "Kimi-K2.6" --sequential

# Run only Tax tasks
python -m backend.rerun_model --models "alawyer" --category "Tax" --max-workers 2

# Run only calculation tasks under Austrian Tax Law
python -m backend.rerun_model --models "alawyer" --task-type "calculation" --regulatory-framework "Austrian Tax Law" --dry-run

# Run only open-ended answer types (best suited for Alawyer)
python -m backend.rerun_model --models "alawyer" --answer-type "open_text,journal_entry" --max-workers 1

# Re-run specific tasks by ID (exact, prefix, and range — comma-separated, mix freely)
python -m backend.rerun_model --models "Kimi-K2.6" --question-ids "11908783_0028"
python -m backend.rerun_model --models "Kimi-K2.6" --question-ids "11908783"
python -m backend.rerun_model --models "Kimi-K2.6" --question-ids "11908783_0001:11908783_0050"
python -m backend.rerun_model --models "Kimi-K2.6" --question-ids "11908783,12345678_0001:12345678_0010"

# Re-run specific tasks by BenchmarkTask.id (exact and range — comma-separated, mix freely)
python -m backend.rerun_model --models "Kimi-K2.6" --task-ids "19"
python -m backend.rerun_model --models "Kimi-K2.6" --task-ids "13:543,1000:1199"
```

### 9.4 Recommended max-workers by model count

| Models being re-run | Recommended max-workers | Connections used |
|---|---|---|
| 1 | 15 | 15 |
| 3 | 15 | 45 |
| 13 | 4 | 52 |

### 9.5 How outputs are linked

The script creates a new `Submission` row for each task with `task_id` pointing to the existing task. The pipeline then writes `benchmark_outputs` rows linked to that `task_id` — exactly the same as a normal run. The new model's results are fully integrated with all existing results in the database.

### 9.6 Skip logic

Before creating any submission, the script queries `benchmark_outputs` for existing rows matching the requested model(s). If all requested models already have outputs for a task, that task is skipped. Running the script twice for the same model is completely safe — the second run does nothing.

Note the skip test is **existence-only**: a row that exists but holds an empty `final_answer` (a genuine model failure) still counts as "done" and is skipped. To force such a row to be re-answered, delete it first so the task looks incomplete again.

**`--dry-run` validates the whole selection**

In `--dry-run`, `rerun_model.py` validates **every task the filters matched**, not only the tasks that would run. It therefore doubles as a data-quality report over any slice of the dataset:

```bash
# audit one matrikelnummer's tasks without running anything
python -m backend.rerun_model --models "gpt-5-mini" --question-ids "12015528" --dry-run

# audit the entire dataset
python -m backend.rerun_model --models "gpt-5-mini" --dry-run
```

This still reports `OPTS`/`GOLD`/`TOL`/`MISS`/`TYPE` findings when nothing needs running — earlier versions returned early in that case and validated nothing.

### 9.7 Shared utilities (`batch_utils.py`)

Both `batch_run.py` and `rerun_model.py` import shared helpers from `backend/batch_utils.py`:

| Helper | Description |
|---|---|
| `create_submission()` | Creates a pending Submission row |
| `ensure_batch_user()` | Creates the batch user in DB if missing |
| `get_existing_model_outputs()` | Checks which models already have outputs for a task |
| `log_summary()` | Standardised run summary |
| `setup_error_log(script_name)` | Adds a WARNING+ `FileHandler` to the root logger; writes `logs/<script_name>_errors_<timestamp>.log`. Called automatically at the start of every run. |
| `check_field_consistency(tasks)` | The data-quality gate. Validates `answer_type`, judge inputs (`grading_criteria`, `numeric_tolerance` incl. parseability), and choice-task option/gold integrity. Emits `TYPE`/`MISS`/`TOL`/`OPTS`/`GOLD` codes — see §8.3. Called during `--dry-run` by both scripts. |
| `check_attached_files()` | Checks which attached file paths can be resolved (dry-run only) |
| `check_pdf_readability()` | Opens each local PDF with PyMuPDF and warns if no text is extractable (scanned image PDF); same condition that raises `PDF_NO_TEXT` at runtime (dry-run only) |
| `resolve_attached_files()` | Resolves attached file paths for real runs |
| `test_endpoints()` | Probes each model's API endpoint (dry-run only) |
| `BATCH_USER_ID` / `BATCH_USER_EMAIL` | Shared constants |

---

### 9.8 Pre-computed Results Importer (`import_precomputed_results.py`)

`backend/import_precomputed_results.py` imports **already-scored model outputs** from an Excel file produced by an external run (e.g. a colleague's own offline evaluation script). Unlike `batch_run.py` and `rerun_model.py`, it **never calls a model API or the judge** — it writes `benchmark_runs` / `benchmark_outputs` rows (and, in the default mode, `benchmark_tasks` rows too) directly from the spreadsheet data. Use it when someone hands you a finished results file instead of a task-only Excel to run through the live pipeline.

**Two supported Excel layouts**, selected by the `--outputs-only` flag:

| Mode | Sheets required | Task handling |
|---|---|---|
| Default | `Questions` + `Outputs` (or whatever `--questions-sheet`/`--outputs-sheet` point to) | Tasks are upserted by `question_id` via `upsert_task()`, same as `batch_run.py` |
| `--outputs-only` | Just the output sheet — no task sheet at all | Tasks must **already exist** in the DB; looked up by `question_id`. A task missing from the DB is reported as an error for that row, never fabricated |

Use `--outputs-only` when backfilling results for tasks that were already imported previously (e.g. adding "old model" results against the original 521-task dataset) — task metadata is left completely untouched, only `benchmark_runs`/`benchmark_outputs` rows are added.

Output sheet columns (either mode) — one row per `(question_id, model)` pair: `Model`, `question_id`, `model_answer_1/2/3`, `model_confidence_1/2/3`, `final_answer`, `avg_model_confidence`, `score_percent_sc_mc`, `judge_score_percent`, `judge_confidence`, `final_score_percent`, `evaluation_method`, `token_input`, `token_output`, `token_reasoning`, `evaluated_at_utc`, `evaluation_notes`.

**All flags:**

| Flag | Default | Description |
|---|---|---|
| `--file` | *(required)* | Path to the Excel file |
| `--questions-sheet` | `Questions` | Sheet name for tasks. Ignored with `--outputs-only` |
| `--outputs-sheet` | `Outputs` | Sheet name for model outputs |
| `--outputs-only` | off | Skip the Questions sheet — look up existing tasks in the DB by `question_id` instead of upserting them |
| `--dry-run` | off | Parse + validate only — no DB writes |
| `--limit` | off | Only process the first N tasks (useful for testing) |
| `--user` | `batch_admin` | User ID to attribute submissions to |
| `--rename-model` | *(none)* | Rename a model on import, e.g. `"DeepSeek-V3.2-2:DeepSeek-V3.2"`. Repeatable. Applied on top of `DEFAULT_RENAMES` in the script (used to fold naming variants from an external run into the model name already used elsewhere in the DB) |
| `--skip-existing` | off | Skip `(task, model)` pairs that already have a `benchmark_output` row — same dedup logic as `rerun_model.py`, via `get_existing_model_outputs()` |

**Validation (runs on every invocation, dry-run or not):** for every task, confirms there's at least one matching row in the output sheet, flags missing models and duplicate `(question_id, model)` rows before anything is written. With `--outputs-only`, also confirms every `question_id` already resolves to a task in the DB.

**What gets written per task:**
- Default mode only: one `BenchmarkTask` row (via the same `upsert_task()` used by `batch_run.py` — `source="batch_import"`, `is_public=True`, `validation_status="approved"`). `--outputs-only` skips this entirely — the existing task row is untouched.
- One `Submission` row, set directly to `status="done"` with `completed_at` set (no pending → processing → done flow, since there's no live run to track)
- One shared `run_id` per task (`run_import_<timestamp>_<uuid8>`), used across all of that task's models — matches the same semantics `run_pipeline()` uses (`run_id` groups the models run together *for one task*)
- One `BenchmarkRun` + one `BenchmarkOutput` row per model, populated straight from the matching output row (`judge_token_input`/`judge_token_output` are left `null` if the source sheet doesn't have them). `inference_notes` records the source filename, e.g. `"Imported from output_old_models.xlsx (external run)"`

```bash
# Pre-flight check — no DB writes, no API calls
python -m backend.import_precomputed_results --file backend/uploads/results_IFRS_n44.xlsx --dry-run

# Test on the first 2 tasks
python -m backend.import_precomputed_results --file backend/uploads/results_IFRS_n44.xlsx --limit 2

# Full import
python -m backend.import_precomputed_results --file backend/uploads/results_IFRS_n44.xlsx

# Re-run safely after a partial import — already-imported (task, model) pairs are skipped
python -m backend.import_precomputed_results --file backend/uploads/results_IFRS_n44.xlsx --skip-existing

# Fold an extra model-naming variant into an existing model name on import
python -m backend.import_precomputed_results --file backend/uploads/results.xlsx --rename-model "gpt-5.4-preview:gpt-5.4"

# Outputs-only — backfill results for "old" models against tasks that already exist in the DB
python -m backend.import_precomputed_results --file backend/output_old_models.xlsx --outputs-sheet Output --outputs-only --dry-run
python -m backend.import_precomputed_results --file backend/output_old_models.xlsx --outputs-sheet Output --outputs-only --skip-existing
```

Attached files referenced in the `Questions` sheet (default mode only) are resolved the same way as in `batch_run.py` — via `resolve_attached_files()`, recursively searching `backend/uploads/` by filename if the original (often external-machine) absolute path doesn't exist locally. See §8.9.

---

### 9.9 Maintenance scripts (one-off data repairs)

Three read-then-repair scripts for defects that predate the current safeguards. All three follow the same conventions: `--dry-run` prints the full diff and writes nothing, `--yes` skips the confirmation prompt, and all are **idempotent** — on a clean database each reports "nothing to do", so they are safe to re-run any time.

| Script | Fixes | Reusable? |
|---|---|---|
| `dedup_outputs.py` | Duplicate `(task_id, model_name)` rows in `benchmark_outputs`, keeping the **earliest** `evaluated_at_utc` and deleting later ones; also removes orphaned `benchmark_runs` rows left by abandoned attempts | Largely historical — the §3.3 constraint prevents new duplicates |
| `backfill_sc_mc_scores.py` | Stale `score_percent_sc_mc` / `final_score_percent` on choice tasks, by recomputing with the current `score_sc_mc_percent()` from the already-stored `final_answer` (no API calls) | Yes — safe after any scoring-logic change |
| `fix_broken_options.py` | Tasks whose `options` are stuck as `{"raw": ...}`, by re-parsing with the current `parse_options()`. Flags but never touches anything still unparseable | Yes |

```bash
python -m backend.dedup_outputs --dry-run
python -m backend.backfill_sc_mc_scores --dry-run
python -m backend.fix_broken_options --dry-run
# then re-run with --yes to apply
```

> Run `dedup_outputs.py` **before** applying migration `a3f9c1d8e2b7` on any database that still contains duplicates — the UNIQUE constraint cannot be created while they exist.

### 9.10 Per-task model scoping in `rerun_model.py`

When `--models` names several models and a task is missing only *some* of them, only the missing ones are called. `process_task()` sets `pipeline.MODEL_LIST_OVERRIDE` to that task's `models_needed` list for the duration of its `run_pipeline()` call:

```python
token = MODEL_LIST_OVERRIDE.set(models_needed)
try:
    pipeline_status = run_pipeline(sub.id)
finally:
    MODEL_LIST_OVERRIDE.reset(token)
```

`OPENAI_MODEL_LIST` is deliberately **not** set process-wide by this script. Previously it was, which meant `run_pipeline()` re-ran *every* requested model for any task that needed even one — wasting API spend and (before §3.3) inserting duplicate rows with conflicting scores. `contextvars` are thread-local, so this stays correct under `--max-workers > 1`.

You can confirm the scoping in the log — each task reports only what it actually needs:

```
[1/5] [RUN] 12008933_0001 → submission 2820 — models: ['gpt-5-mini', 'claude-opus-4-8']
[2/5] [RUN] 12008933_0042 → submission 2822 — models: ['gpt-5-mini']
```

---

## 10. Frontend Pages

### 10.1 Public Site (`public/`)

Five static HTML pages served directly. No authentication required. Navigation uses a blue page-tabs bar that switches between in-page sections using `showPage()` JavaScript calls. All five pages have a **Sign In** button added to the page-tabs bar that navigates to `auth-pages/sign-in.html`.

| File | Purpose |
|---|---|
| `index.html` | Overview, ticker bar with live scores, summary statistics. |
| `leaderboard.html` | Full results table with all models and categories. |
| `dashboard.html` | Visual analytics and score breakdowns. |
| `methodology.html` | Explanation of SC/MC formula and LLM judge scoring. |
| `about.html` | Project team and institutional affiliations. |

---

### 10.2 Auth Pages (`auth-pages/`)

Each page is a plain HTML file with no inline JavaScript. Logic lives in a matching `.js` file.

| File | Purpose |
|---|---|
| `config.js` | **The only file to edit when deploying.** Sets `API`, `CLERK_PUBLISHABLE_KEY`, and `CLERK_JS_URL`. Loaded first on every page. |
| `auth-pages.js` | Shared utilities used by all pages. Also injects the Clerk `<script>` tag dynamically using values from `config.js`. |
| `sign-in.html` / `sign-in.js` | Email + password login. Handles new-device verification code step. Redirects to `landing.html` on success. |
| `register.html` / `register.js` | Registration form. Domain pre-check before Clerk account creation. GDPR consent checkbox required. |
| `landing.html` / `landing.js` | Protected home page. Shows welcome message and submission history grid. Nav bar has Account Settings, Sign Out, and (admin only) Admin Panel buttons. Logo links back to `landing.html` on all auth pages. |
| `upload.html` / `upload.js` | Task contribution form. Supports up to 3 PDF and 3 Excel uploads (20 MB each). GDPR data-use consent required. On submit: shows "Preparing Payment" spinner, polls until `checkout_url` is ready, then redirects to Stripe. |
| `payment-success.html` / `payment-success.js` | Shown after Stripe payment. Calls `/confirm-payment`, shows benchmark progress, redirects to `results.html` when done. |
| `account.html` / `account.js` | Account settings page. Displays profile (name, email). Danger Zone section with two-step confirmation for permanent account deletion — deletes all local DB data first, then removes the user from Clerk. |
| `admin.html` / `admin.js` | Admin-only panel. Auth-guarded — redirects to `landing.html` if not admin. Four sections: Task Review (approve/reject with expandable detail rows), Users (activate/deactivate), Stats (live KPI cards), Domains (add/remove allowed domains). |
| `results.html` | Dedicated result viewer. If `done` shows results from database immediately; if `processing` polls every 3 seconds. Never re-runs the benchmark. |

---

### 10.3 Public Site Data Layer (`results.js` + `data.js`)

The public site is fully dynamic — all numbers, charts, tables, and leaderboards are driven from two files. **Never edit numbers directly in the HTML files.**

#### `results.js` — single source of truth

Contains `BENCHMARK_RESULTS` (one object per model) and `BENCHMARK_META` (dataset composition). To add a new model or update scores, edit only this file.

**To add a new model:**
1. Copy any existing model block
2. Fill in all fields (see field reference at top of file)
3. Insert at the correct position (sorted by `overall` descending)
4. Everything updates automatically — ticker, leaderboard, holistic matrix, cost table, token bars, all charts

**Key fields per model:**

| Field | Description |
|---|---|
| `overall`, `tax`, `financial`, `management` | Category scores (%) |
| `interpLaw`, `calculation`, `journal` | Task type scores (%) |
| `multiChoice`, `openText`, `singleChoice`, `journalEntry` | Answer type scores (%) |
| `austrianTax`, `mixedAcc`, `ugb`, `ifrs` | Regulatory framework scores (%) |
| `eduProf`, `eduMaster`, `eduVoc` | Education level scores (%) |
| `n` | Tasks completed, e.g. `'520'` or `'465/520'` |
| `priceIn`, `priceOut` | Token prices in USD per 1M tokens |
| `cost` | Pre-calculated avg cost per task in USD |
| `tokTask` | Average tokens per task |
| `speed` | Output tokens/sec |
| `calib` | Confidence calibration points `[{x, y, n}]` |
| `note` | Optional warning shown in leaderboard |

**To update dataset composition** (`BENCHMARK_META.categories`, `taskTypes`, `questionFormats`, `educationLevels`, `regulatoryFrameworks_data`): change the `tasks` count — percentages recalculate automatically.

#### Recomputing scores from a fresh Excel export (`recompute_results.py`)

When a colleague hands you a full/partial rerun as an Excel file with `benchmark_tasks` + `benchmark_outputs` sheets (same column layout as the DB tables — `category`, `task_type`, `answer_type`, `regulatory_framework`, `education_level` on the tasks sheet; `model_name`, `final_score_percent`, `token_input`, `token_output`, `token_reasoning`, `avg_model_confidence`/`judge_confidence` on the outputs sheet), don't hand-edit `results.js` — use:

```bash
python -m backend.recompute_results
```

Edit the `XLSX_PATH` and `UPDATED_MODELS` constants at the top of the script first (which file to read, and which model names in the array should actually get replaced). The script then:

1. Recomputes every score field (category/task-type/answer-type/regulatory-framework/`byEdu`/`n`/`cost`/`tokTask`/`calib`) per model directly from the Excel rows, using exact-string-match masks (a hybrid/unknown `task_type`, `answer_type`, or `regulatory_framework` value counts toward `overall` only, matching the site's existing convention — e.g. `open_numeric` answers or `interpretation_of_law_and_journal_entry` tasks).
2. **Diffs every model NOT in `UPDATED_MODELS`** against the current `results.js` and refuses to write if any of their score fields differ — this is the safety gate that catches an export covering more models than you expected.
3. Re-sorts the full array by `overall` descending and rewrites `public/results.js`, leaving `BENCHMARK_META` and the untouched models' object bodies byte-for-byte identical (only their comment-header rank number may change).

`priceIn`, `priceOut`, and `speed` are always carried over unchanged from the current file — these exports carry no pricing/timing data, so update them by hand if pricing changed. `token_reasoning` is folded into `token_output` for some models but additive for others (see `ADD_REASONING_TOKENS` in the script) — verify this per-model assumption before trusting `tokTask`/`cost` for a model not already in that mapping.

#### `data.js` — render functions

Contains all DOM render functions. These are called once on page load and build the entire UI from `BENCHMARK_RESULTS`. Do not edit unless changing layout or adding new visualisations.

| Function | What it renders |
|---|---|
| `renderTicker()` | Scrolling score bar at the top |
| `renderOverviewLeaderboard()` | Desktop leaderboard table (sorted by overall) |
| `renderHolisticMatrix()` | Full results matrix with grouped headers |
| `renderCostTable()` | API Cost Analysis table |
| `renderTokenBars()` | Avg. Token Usage bar chart |
| `renderQuestionDistribution()` | Donut chart + legend |
| `renderDatasetTables()` | All dataset composition tables |

---

All shared utilities used across multiple auth pages are in `auth-pages/auth-pages.js`. Every HTML page loads `config.js` first, then `auth-pages.js`. The Clerk `<script>` is no longer hardcoded in HTML — `auth-pages.js` injects it dynamically on load using `CLERK_PUBLISHABLE_KEY` and `CLERK_JS_URL` from `config.js`.

| Function / Variable | Description |
|---|---|
| *(startup)* | Injects the Clerk `<script>` tag dynamically using values from `config.js`. |
| `waitForClerk(callback)` | Polls every 100ms until `window.Clerk.load` is available. Handles async script loading reliably. |
| `showError(id, msg)` | Shows a red error banner by element ID. |
| `showSuccess(id, msg)` | Shows a green success banner by element ID. |
| `hideMessages(ids)` | Hides an array of message banner elements. |
| `setLoading(btnId, bool, label)` | Toggles button loading state with a spinner. |
| `escHtml(text)` | Escapes user content before inserting into HTML (XSS prevention). |
| `handleClerkError(err, id)` | Maps Clerk technical errors to friendly user-facing messages. |
| `showStep(id)` | Switches between `.auth-step` divs (used in multi-step forms). |
| `setupCodeInput(inputId, fn)` | Configures 6-digit code inputs with auto-submit on completion. |
| `handleSignOut()` | Signs out via Clerk and redirects to `sign-in.html`. Available globally on all auth pages. |

---

## 11. Environment Setup

### 11.1 Prerequisites

- Python 3.11 or newer
- A Clerk account (free tier at [clerk.com](https://clerk.com))
- A Stripe account (free at [stripe.com](https://stripe.com))

---

### 11.2 Python Dependencies

Install all packages with:

```bash
python -m pip install fastapi uvicorn sqlalchemy alembic psycopg2-binary \
    python-dotenv aiofiles python-multipart pandas openpyxl pymupdf \
    requests openai anthropic "PyJWT[crypto]" stripe slowapi
```

---

### 11.3 Environment Variables (`.env`)

Create `.env` in the project root with the following variables:

| Variable | Description |
|---|---|
| `DATABASE_URL` | SQLite path for local dev. Use absolute path if OneDrive/spaces in path. |
| `CLERK_PUBLISHABLE_KEY` | `pk_test_...` key from Clerk dashboard → API Keys. |
| `CLERK_SECRET_KEY` | `sk_test_...` key from Clerk dashboard → API Keys. |
| `CLERK_PEM_PUBLIC_KEY` | RSA public key from Clerk dashboard → API Keys → JWT verification key. |
| `CLERK_JWKS_URL` | Optional. Set to override the auto-derived JWKS URL. |
| `ADMIN_EMAIL` | Your own email address. Required for admin endpoints. |
| `UPLOAD_DIR` | Path where uploaded files are saved. Default: `./uploads` |
| `ALLOWED_ORIGINS` | Comma-separated CORS-allowed origins. Defaults to localhost dev URLs if unset. |
| `APP_ENV` | Set to `production` to disable auto-`create_all()` on startup. Default: `development`. |
| `APP_VERSION` | API version string shown in `/health` and `/docs`. Default: `1.0.0`. |
| `DEBUG_PIPELINE` | Set to `true` to enable DEBUG logging for the pipeline (prompts + raw responses). Default: off. |
| `OPENAI_MODEL_LIST` | Comma-separated list of model names to benchmark. Also used as fallback by `rerun_model.py --models`. |
| `MODEL_REGISTRY_JSON` | JSON object mapping model names to API config (base_url, api_key, api_type, timeout). |
| `ALAWYER_API_KEY` | API key for the Alawyer Austrian legal AI. Referenced in `MODEL_REGISTRY_JSON` as `${ALAWYER_API_KEY}`. |
| `BATCH_USER_ID` | User ID used for batch-imported submissions. Default: `batch_admin`. |
| `BATCH_USER_EMAIL` | Email for the batch user. Default: `batch@accountingbench.local`. |
| `DEFAULT_PRICE_CENTS` | Default submission price in cents if the `settings` table row has no price set. Default: `5000` (€50). |
| `DEFAULT_CURRENCY` | Default currency for Stripe. Default: `eur`. |
| `STRIPE_SECRET_KEY` | Stripe secret key (`sk_test_...` for testing, `sk_live_...` for production). |
| `STRIPE_PUBLISHABLE_KEY` | Stripe publishable key (for reference — not used server-side). |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook secret. Optional — not used in current implementation. |
| `FRONTEND_URL` | Base URL of the frontend. Stripe uses this for payment success/cancel redirects. **See §7.3 for details.** |

Example `.env` file:

```
DATABASE_URL=sqlite:///C:/Users/yourname/path/to/backend/accountingbench.db

CLERK_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
CLERK_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
CLERK_PEM_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA...
-----END PUBLIC KEY-----"

ADMIN_EMAIL=your-admin@institution.ac.at
UPLOAD_DIR=./uploads

OPENAI_API_KEY=not-used
OPENAI_MODEL_LIST=claude-opus-4-7,gpt-5.5,Kimi-K2.6

MODEL_REGISTRY_JSON='{
  "claude-opus-4-7": { ... },
  ...
}'

BATCH_USER_ID=batch_admin
BATCH_USER_EMAIL=admin@wu.ac.at

STRIPE_SECRET_KEY=sk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
STRIPE_WEBHOOK_SECRET=

# Local development — must use 127.0.0.1 (not localhost) — see §7.3
FRONTEND_URL=http://127.0.0.1:5500
```

---

### 11.4 Database Initialisation (run once)

Run these commands from the root `accountingbench/` folder:

```bash
# 1. Run database migrations (creates all tables, the checkout_url column, and
#    the UNIQUE (task_id, model_name) constraint on results — see §3.3).
#    On an existing DB that still has duplicates, run backend/dedup_outputs.py
#    first: the constraint cannot be created while duplicates exist.
python -m alembic -c backend/alembic.ini upgrade head

# 2. Import the 521 original tasks from the Excel spreadsheet
python import_tasks.py --excel backend/matrikelnummer_ground_truth_template.xlsx

# 3. Add your first allowed email domain
python -c "
from backend.database import SessionLocal
from backend.models import AllowedDomain
from datetime import datetime
db = SessionLocal()
db.add(AllowedDomain(domain='wu.ac.at', added_at=datetime.now(), added_by='admin'))
db.commit()
db.close()
print('Done')
"
```

---

### 11.5 Running the Server

Always run from the root `accountingbench/` folder — never from inside `backend/`:

```bash
python -m uvicorn backend.main:app --reload --port 8000
```

The server starts at `http://127.0.0.1:8000`. The `--reload` flag restarts automatically on file changes.

Open the interactive API documentation at `http://127.0.0.1:8000/docs` to test all endpoints directly in the browser.

---

### 11.6 Running the Frontend

Serve the frontend with Python's built-in HTTP server:

```bash
python -m http.server 5500
```

Pages are served at `http://127.0.0.1:5500/auth-pages/sign-in.html`.

> ⚠️ **Do not use VS Code Live Server for payment testing.** Live Server automatically reloads the browser on every file save in VS Code, which interrupts in-flight Stripe polling loops. Python's `http.server` serves files statically without any auto-reload.

> ⚠️ **Always open the root `accountingbench/` folder** before starting the server, not a subfolder. The pages reference `../public/styles.css` — relative paths break if you serve from a subfolder.

---

### 11.7 Windows-Specific and macOS Notes

**Windows:**
- Always use `python -m uvicorn` and `python -m alembic` instead of bare `uvicorn` and `alembic`.
- If your path contains spaces (e.g. `OneDrive - WU Wien`), use an absolute path in `DATABASE_URL` with forward slashes:
  ```
  DATABASE_URL=sqlite:///C:/Users/yourname/OneDrive - WU Wien/Dokumente/AccountingBench/backend/accountingbench.db
  ```
- Always run Python commands from the root `accountingbench/` folder, not from inside `backend/`.
- Use `127.0.0.1` everywhere instead of `localhost` — on Windows, `localhost` resolves to IPv6 (`::1`) which conflicts with Clerk's origin matching.

**macOS:**
- Use `python -m pip install <package>` instead of `pip install` to ensure packages install for the correct Python version (especially important if using pyenv).
- For an absolute SQLite path, use 4 slashes: `sqlite:////Users/yourname/Documents/AccountingBench/backend/accountingbench.db`
- To create a `.env` file (dotfiles are hidden in Finder), use Terminal: `touch .env` then edit in VS Code.
- If you get `ModuleNotFoundError` for any package, always use `python -m pip install <package>` to guarantee it installs for the Python version returned by `python --version`.

---

## 12. Clerk Configuration

### 12.1 Dashboard Settings

In the Clerk dashboard at [clerk.com](https://clerk.com), configure the following settings:

**User & Authentication → Email, Phone, Username:**
- Enable **Email address** as the identifier
- Enable **Password**
- Disable **Email verification code** as a sign-in method (otherwise users are asked for a code on every sign-in instead of using their password)

**API Keys:**
- Copy the **Publishable key** (`pk_test_...`) → add to `.env` as `CLERK_PUBLISHABLE_KEY` AND to `auth-pages/config.js` as `CLERK_PUBLISHABLE_KEY`
- Copy the **Secret key** (`sk_test_...`) → add to `.env` as `CLERK_SECRET_KEY`
- Copy the **JWT verification key** (RSA public key) → add to `.env` as `CLERK_PEM_PUBLIC_KEY`
- Copy the **Clerk JS URL** (the `src` from the Clerk script snippet in the dashboard) → add to `auth-pages/config.js` as `CLERK_JS_URL`

---

### 12.2 JWT Template (Required)

Without the email claim in the JWT, the domain check in `auth.py` fails with a 403 error. Without `first_name`/`last_name`, the user's name will be `null` in the database.

In the Clerk dashboard → **Configure** → **Sessions** → **"Customize session token"**, add these claims:

```json
{
  "email": "{{user.primary_email_address}}",
  "first_name": "{{user.first_name}}",
  "last_name": "{{user.last_name}}"
}
```

> **Note on existing users:** If you added `first_name`/`last_name` to the JWT template after users had already registered, their names in the database will be `null`. `auth.py` automatically backfills missing names on the user's next login — no manual database update needed.

---

### 12.3 Frontend Configuration (`config.js`)

All frontend configuration lives in `auth-pages/config.js`. This is the **only file you need to edit** when setting up a new environment or deploying to production.

```javascript
// auth-pages/config.js

// Backend API URL
var API = 'http://127.0.0.1:8000';           // development
// var API = 'https://your-api.onrender.com'; // production

// Clerk publishable key — from Clerk dashboard → API Keys
var CLERK_PUBLISHABLE_KEY = 'pk_test_...';

// Clerk JS URL — from Clerk dashboard → API Keys → Clerk SDK snippet
// The subdomain (e.g. amused-hyena-99) is unique to your Clerk instance
var CLERK_JS_URL = 'https://your-instance.clerk.accounts.dev/npm/@clerk/clerk-js@latest/dist/clerk.browser.js';
```

The Clerk `<script>` tag is **no longer hardcoded in any HTML file**. `auth-pages.js` reads these values and injects the script dynamically on page load, so there is nothing to update in the HTML files themselves.

---

## 13. Remaining Implementation

### Phase 5 — Live Leaderboard

Update `public/main.js` to fetch from `GET /api/leaderboard` instead of reading from `data.js`. The endpoint is already implemented in `main.py` and returns data in the same format as the existing `lbData` array.

> **Note:** The real benchmark pipeline (`pipeline.py`) and batch runner (`batch_run.py`) are already implemented. See §6 and §8 for details.

---

### Phase 6 — Deployment to Render

Deploy the FastAPI backend as a **Render Web Service** and the static HTML files as **Render Static Sites**. Key changes needed:

1. Switch `DATABASE_URL` in `.env` to the Render PostgreSQL connection string
2. In `auth-pages/config.js`, update all three values for production:
   ```javascript
   var API                  = 'https://your-api.onrender.com';
   var CLERK_PUBLISHABLE_KEY = 'pk_live_...';   // or keep pk_test_ if still testing
   var CLERK_JS_URL          = 'https://your-instance.clerk.accounts.dev/...';
   ```
3. Set `FRONTEND_URL` in `.env` to the Render static site URL (e.g. `https://your-site.onrender.com`) — this updates Stripe's success/cancel redirect URLs automatically
4. Add the Render backend and frontend URLs to the `ALLOWED_ORIGINS` list in `main.py`
5. The JWKS fallback in `auth.py` will work automatically on Render (unrestricted internet access)
6. Run `alembic upgrade head` on the Render database on first deploy

---

## 14. Database Administration (SQL Reference)

The admin panel (`admin.html`) covers most day-to-day operations. The SQL queries below are useful for bulk operations, scripting, or direct database access via **DB Browser for SQLite** (free at [sqlitebrowser.org](https://sqlitebrowser.org)).

Open `backend/accountingbench.db`, click the **Execute SQL** tab, and run the queries below.

### Find pending submissions

```sql
SELECT bt.question_id, bt.prompt, bt.category, bt.answer_type, s.status, s.submitted_at
FROM submissions s
JOIN benchmark_tasks bt ON bt.id = s.task_id
WHERE bt.validation_status = 'pending'
ORDER BY s.submitted_at DESC;
```

### Approve a single task

```sql
UPDATE benchmark_tasks
SET is_public = 1,
    validation_status = 'approved',
    validated_by = 'admin@wu.ac.at'
WHERE question_id = 'usr_3a9f12';
```

Replace `usr_3a9f12` with the actual `question_id` and `admin@wu.ac.at` with your email.

### Reject a single task

```sql
UPDATE benchmark_tasks
SET is_public = 0,
    validation_status = 'rejected',
    validated_by = 'admin@wu.ac.at'
WHERE question_id = 'usr_3a9f12';
```

### Approve all pending user submissions at once

```sql
UPDATE benchmark_tasks
SET is_public = 1,
    validation_status = 'approved',
    validated_by = 'admin@wu.ac.at'
WHERE source = 'user_submitted'
AND validation_status = 'pending';
```

After running any query, click **Write Changes** in DB Browser to save.

> **Effect of approval:** Setting `is_public = 1` includes the task in `GET /api/leaderboard` calculations automatically — no server restart needed.

---

*AccountingBench Developer Documentation · Version 2.0 · July 2026*
*WU Vienna · Financial Accounting & Auditing Group · Board Service Center*
