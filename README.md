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
7. [Frontend Pages](#7-frontend-pages)
8. [Environment Setup](#8-environment-setup)
9. [Clerk Configuration](#9-clerk-configuration)
10. [Remaining Implementation](#10-remaining-implementation)

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
| Frontend — public | Static HTML + CSS + vanilla JavaScript |
| Frontend — portal | Static HTML pages served via VS Code Live Server (port 5500) |
| File storage | Local filesystem (`uploads/` folder) |
| Deployment target | Render.com (Phase 6 — not yet implemented) |
| Payments | Stripe (Phase 7 — not yet implemented) |

---

### 1.2 Current Implementation Status

| Feature | Status | Notes |
|---|---|---|
| Database schema + migrations | ✅ Done | 7 tables, Alembic migrations applied |
| 521 original tasks imported | ✅ Done | From `matrikelnummer_ground_truth_template.xlsx` |
| FastAPI server | ✅ Done | 14 endpoints, running locally |
| Clerk authentication | ✅ Done | JWT verification via local PEM key + JWKS fallback |
| Domain restriction | ✅ Done | Checked against `allowed_domains` table on every request |
| Sign-in page | ✅ Done | Custom form calling Clerk API directly |
| Register page | ✅ Done | Domain pre-check before Clerk account creation |
| Landing page | ✅ Done | Shows user's submission history |
| Upload form | ✅ Done | All task fields, file uploads, validation |
| Results page | ✅ Done | Dedicated page, pulls from database, no re-run |
| Dummy pipeline | ✅ Done | Always returns 100%, saves to database |
| Admin review page | ⏳ Planned | Phase 4 |
| Real benchmark script | ⏳ Planned | Phase 5 |
| Live leaderboard | ⏳ Planned | Phase 5 |
| Deployment to Render | ⏳ Planned | Phase 6 |
| Stripe payments | ⏳ Planned | Phase 7 |

---

## 2. File Structure

### 2.1 Complete Directory Tree

```
accountingbench/
├── public/                        ← Public static site (served as-is)
│   ├── index.html                 ← Overview / home page
│   ├── leaderboard.html           ← Public leaderboard
│   ├── dashboard.html             ← Analytics dashboard
│   ├── methodology.html           ← Methodology explanation
│   ├── about.html                 ← About the project
│   ├── styles.css                 ← Global CSS (public + auth pages)
│   ├── main.js                    ← Public site JavaScript
│   ├── data.js                    ← Hardcoded leaderboard data (temporary)
│   └── img/                       ← Logos and images
│
├── auth-pages/                    ← Private authenticated pages
│   ├── auth-pages.js              ← Shared JS utilities
│   ├── sign-in.html               ← Login page
│   ├── register.html              ← Registration page
│   ├── landing.html               ← User's submission history
│   ├── upload.html                ← Task contribution form
│   └── results.html               ← Benchmark result viewer
│
└── backend/                       ← FastAPI Python server
    ├── main.py                    ← App entry point, all endpoints
    ├── auth.py                    ← Clerk JWT verification + domain check
    ├── database.py                ← SQLAlchemy engine + session factory
    ├── models.py                  ← 7 database table definitions
    ├── submissions.py             ← POST /submissions/prepare endpoint
    ├── import_tasks.py            ← One-time Excel → database migration
    ├── processing/
    │   └── dummy_pipeline.py      ← Test pipeline (always returns 100%)
    ├── migrations/                ← Alembic migration files
    │   └── versions/              ← Auto-generated migration scripts
    ├── accountingbench.db         ← SQLite database (local dev only)
    ├── uploads/                   ← User-uploaded files
    │   └── {user_id}/{sub_id}/    ← Per-submission file storage
    ├── alembic.ini                ← Alembic configuration
    ├── .env                       ← Environment variables (never commit)
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
| `settings` | Single-row config table (pricing for Phase 7). |

---

### 3.2 Key Table Details

#### `benchmark_tasks`

This table replaces the ground-truth Excel spreadsheet. Column names match the spreadsheet exactly so the Python benchmark script can consume rows without changes.

| Field | Description |
|---|---|
| `question_id` | Unique ID. Format: `usr_xxxxxx` for user submissions, `q_NNNN` for originals. |
| `source` | `"original_dataset"` for the 521 imported tasks, `"user_submitted"` for new contributions. |
| `is_public` | `False` by default. Set to `True` by admin when task is approved for the leaderboard. |
| `validation_status` | `"approved"` \| `"pending"` \| `"rejected"` |
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

#### `submissions`

Tracks each user contribution lifecycle.

| Status | Meaning |
|---|---|
| `pending` | Saved, waiting for benchmark to start. |
| `processing` | Pipeline is currently running. |
| `done` | Script finished, scores available in database. |
| `error` | Script encountered an error. |

> **Note:** Payment fields (`payment_status`, `stripe_payment_id`, `price_charged`) are included now so no migration is needed when Stripe is added in Phase 7.

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

The FastAPI server runs at `http://localhost:8000`. Interactive API documentation is available at `http://localhost:8000/docs`.

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
| `GET` | `/me` | Returns the signed-in user's profile. |
| `GET` | `/submissions/mine` | Returns the user's submission history for the landing page. |
| `GET` | `/submissions/{id}/status` | Returns submission status and model scores when done. Polled by `results.html`. |
| `POST` | `/submissions/prepare` | Receives the upload form, saves task + files, triggers pipeline. |

### 5.3 Admin Endpoints (require `ADMIN_EMAIL`)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/admin/tasks?status=pending` | Lists tasks pending review. Also accepts `approved`/`rejected`. |
| `POST` | `/admin/tasks/{id}/approve` | Approves a task — sets `is_public=True` so it appears in the leaderboard. |
| `POST` | `/admin/tasks/{id}/reject` | Rejects a task — stays private. |
| `GET` | `/admin/domains` | Lists all allowed email domains. |
| `POST` | `/admin/domains` | Adds a new allowed domain. Body: `{"domain": "kpmg.com"}`. |
| `DELETE` | `/admin/domains/{id}` | Removes an allowed domain. |

---

## 6. Submission Pipeline

### 6.1 Full Flow

When a user submits a task on `upload.html`, the following happens:

1. `upload.html` validates all required fields in the browser before sending.
2. `POST /submissions/prepare` receives the form data and files.
3. `submissions.py` validates fields again server-side (enum values, conditional requirements, file types and sizes up to 20 MB).
4. A unique `question_id` is generated (format: `usr_xxxxxx`).
5. Uploaded files are saved to `uploads/{user_id}/{submission_id}/`.
6. A row is inserted into `benchmark_tasks` (`is_public=False`, `validation_status=pending`).
7. A row is inserted into `submissions` (`status=pending`).
8. The endpoint returns immediately with `{submission_id, task_id, question_id}`.
9. The browser navigates to `results.html?submission={id}`.
10. The pipeline runs as a FastAPI `BackgroundTask` in a separate thread.
11. `results.html` polls `GET /submissions/{id}/status` every 3 seconds.
12. When `status=done`, the result table is shown from the database — **the script never runs again**.

---

### 6.2 Dummy Pipeline (Testing)

`backend/processing/dummy_pipeline.py` is used during development. It:

- Sets submission status to `"processing"`
- Waits 3 seconds to simulate runtime
- Inserts one `BenchmarkRun` + one `BenchmarkOutput` row for each of the 10 fixed models with `final_score_percent = 100.0`
- Sets submission status to `"done"`

> ✅ **Swapping to the real script:** Change one import line in `submissions.py`:
> ```python
> # Testing (current):
> from backend.processing.dummy_pipeline import run_pipeline
>
> # Production (real script):
> from backend.processing.pipeline import run_pipeline
> ```
> Everything else stays the same.

---

### 6.3 Fixed Model List

The following 10 models are benchmarked for every submitted task:

| Model |
|---|
| gpt-5.4 |
| gpt-5.2 |
| claude-opus-4-6 |
| claude-sonnet-4-6 |
| gpt-5-mini |
| Mistral-Large-3 |
| grok-4-fast |
| gpt-4o |
| DeepSeek-V3.2-2 |
| mercury-2 |

---

## 7. Frontend Pages

### 7.1 Public Site (`public/`)

Five static HTML pages served directly. No authentication required. Navigation uses a blue page-tabs bar that switches between in-page sections using `showPage()` JavaScript calls. All five pages have a **Sign In** button added to the page-tabs bar that navigates to `auth-pages/sign-in.html`.

| File | Purpose |
|---|---|
| `index.html` | Overview, ticker bar with live scores, summary statistics. |
| `leaderboard.html` | Full results table with all models and categories. |
| `dashboard.html` | Visual analytics and score breakdowns. |
| `methodology.html` | Explanation of SC/MC formula and LLM judge scoring. |
| `about.html` | Project team and institutional affiliations. |

---

### 7.2 Auth Pages (`auth-pages/`)

| File | Purpose |
|---|---|
| `sign-in.html` | Email + password login. Handles new-device verification code step when Clerk requires it. Redirects to `landing.html` on success. |
| `register.html` | Registration form. Pre-checks domain against `/auth/check-domain` before creating a Clerk account. Email verification code required. |
| `landing.html` | Protected home page. Shows welcome message with user's first name and a grid of submission cards. Links to `upload.html` and `results.html`. |
| `upload.html` | Task contribution form with three sections: Task Content, Classification & Metadata, Supporting Documents. Navigates to `results.html?submission={id}` on submit. |
| `results.html` | Dedicated result viewer. Checks status immediately on load — if `done` shows results instantly from database, if `processing` shows spinner and polls every 3 seconds. Never re-runs the benchmark. |

---

### 7.3 Shared JavaScript (`auth-pages.js`)

All shared utilities used across multiple auth pages are in `auth-pages/auth-pages.js`. This file is included in every auth page with a `<script src="auth-pages.js"></script>` tag.

| Function | Description |
|---|---|
| `waitForClerk(callback)` | Polls every 100ms until `window.Clerk.load` is available. Handles async script loading reliably. |
| `showError(id, msg)` | Shows a red error banner by element ID. |
| `showSuccess(id, msg)` | Shows a green success banner by element ID. |
| `hideMessages(ids)` | Hides an array of message banner elements. |
| `setLoading(btnId, bool, label)` | Toggles button loading state with a spinner. |
| `escHtml(text)` | Escapes user content before inserting into HTML (XSS prevention). |
| `handleClerkError(err, id)` | Maps Clerk technical errors to friendly user-facing messages. |
| `showStep(id)` | Switches between `.auth-step` divs (used in multi-step forms). |
| `setupCodeInput(inputId, fn)` | Configures 6-digit code inputs with auto-submit on completion. |
| `API` | Global constant: `http://localhost:8000`. Change this for production. |

---

## 8. Environment Setup

### 8.1 Prerequisites

- Python 3.11 or newer
- Node.js (for VS Code Live Server extension)
- VS Code with the **Live Server** extension installed (by Ritwick Dey)
- A Clerk account (free tier at [clerk.com](https://clerk.com))

---

### 8.2 Python Dependencies

Install all packages with:

```bash
python -m pip install fastapi uvicorn sqlalchemy alembic psycopg2-binary \
    python-dotenv aiofiles python-multipart pandas openpyxl pypdf \
    requests openai anthropic "PyJWT[crypto]" stripe
```

---

### 8.3 Environment Variables (`.env`)

Create `backend/.env` with the following variables:

| Variable | Description |
|---|---|
| `DATABASE_URL` | SQLite path for local dev. Use absolute path if OneDrive/spaces in path. |
| `CLERK_PUBLISHABLE_KEY` | `pk_test_...` key from Clerk dashboard → API Keys. |
| `CLERK_SECRET_KEY` | `sk_test_...` key from Clerk dashboard → API Keys. |
| `CLERK_PEM_PUBLIC_KEY` | RSA public key from Clerk dashboard → API Keys → JWT verification key. |
| `CLERK_JWKS_URL` | Optional. Set to override the auto-derived JWKS URL. |
| `ADMIN_EMAIL` | Your own email address. Required for admin endpoints. |
| `UPLOAD_DIR` | Path where uploaded files are saved. Default: `./uploads` |
| `OPENAI_API_KEY` | OpenAI API key (needed by the real benchmark script). |
| `STRIPE_SECRET_KEY` | Stripe secret key — Phase 7 only, leave blank for now. |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook secret — Phase 7 only, leave blank for now. |

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
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
```

---

### 8.4 Database Initialisation (run once)

Run these commands from the root `accountingbench/` folder:

```bash
# 1. Run database migrations (creates all 7 tables)
python -m alembic -c backend\alembic.ini upgrade head

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

### 8.5 Running the Server

Always run from the root `accountingbench/` folder — never from inside `backend/`:

```bash
python -m uvicorn backend.main:app --reload
```

The server starts at `http://localhost:8000`. The `--reload` flag restarts automatically on file changes.

Open the interactive API documentation at `http://localhost:8000/docs` to test all endpoints directly in the browser.

---

### 8.6 Running the Frontend

1. Open the root `accountingbench/` folder in VS Code (not a subfolder).
2. In the VS Code file explorer, navigate to `auth-pages/sign-in.html`.
3. Right-click → **Open with Live Server**.
4. Pages are served at `http://localhost:5500/auth-pages/sign-in.html`.

> ⚠️ **Important:** Always open the root `accountingbench/` folder in VS Code, not the `auth-pages/` subfolder. The pages reference `../public/styles.css` — if the root folder is not open, CSS paths will break.

---

### 8.7 Windows-Specific Notes

- Always use `python -m uvicorn` and `python -m alembic` instead of bare `uvicorn` and `alembic`.
- If your path contains spaces (e.g. `OneDrive - WU Wien`), use an absolute path in `DATABASE_URL` with forward slashes:
  ```
  DATABASE_URL=sqlite:///C:/Users/yourname/OneDrive - WU Wien/Dokumente/AccountingBench/backend/accountingbench.db
  ```
- If SQLAlchemy cannot parse the URL due to spaces, use `database.py` to build the path with `os.path.join(__file__)` instead.
- Always run Python commands from the root `accountingbench/` folder, not from inside `backend/`.

---

## 9. Clerk Configuration

### 9.1 Dashboard Settings

In the Clerk dashboard at [clerk.com](https://clerk.com), configure the following settings:

**User & Authentication → Email, Phone, Username:**
- Enable **Email address** as the identifier
- Enable **Password**
- Disable **Email verification code** as a sign-in method (otherwise users are asked for a code on every sign-in instead of using their password)

**API Keys:**
- Copy the **Publishable key** (`pk_test_...`) → add to `.env` as `CLERK_PUBLISHABLE_KEY`
- Copy the **Secret key** (`sk_test_...`) → add to `.env` as `CLERK_SECRET_KEY`
- Copy the **JWT verification key** (RSA public key) → add to `.env` as `CLERK_PEM_PUBLIC_KEY`

---

### 9.2 JWT Template (Required)

Without the email claim in the JWT, the domain check in `auth.py` fails with a 403 error.

In the Clerk dashboard → **JWT Templates** → **session token**, add this claim:

```json
{
  "email": "{{user.primary_email_address}}"
}
```

---

### 9.3 HTML Page Configuration

Every auth page has two Clerk placeholders that must be replaced with actual values:

```html
<!-- Replace in: sign-in.html, register.html, landing.html, upload.html, results.html -->
<script
  async
  crossorigin="anonymous"
  data-clerk-publishable-key="YOUR_PUBLISHABLE_KEY"
  src="https://unpkg.com/@clerk/clerk-js@latest/dist/clerk.browser.js"
  type="text/javascript">
</script>
```

Replace `YOUR_PUBLISHABLE_KEY` with your `pk_test_...` key. The `unpkg.com` CDN URL does not need to change.

---

## 10. Remaining Implementation

### Phase 4 — Admin Task Review (via SQL)

A dedicated admin UI page is planned for a later phase. In the meantime, tasks can be approved and rejected directly in the database using **DB Browser for SQLite** (free download at [sqlitebrowser.org](https://sqlitebrowser.org)).

Open `backend/accountingbench.db` in DB Browser, click the **Execute SQL** tab, and use the queries below.

#### Find pending submissions

```sql
SELECT bt.question_id, bt.prompt, bt.category, bt.answer_type, s.status, s.submitted_at
FROM submissions s
JOIN benchmark_tasks bt ON bt.id = s.task_id
WHERE bt.validation_status = 'pending'
ORDER BY s.submitted_at DESC;
```

#### Approve a single task

```sql
UPDATE benchmark_tasks
SET is_public = 1,
    validation_status = 'approved',
    validated_by = 'admin@wu.ac.at'
WHERE question_id = 'usr_3a9f12';
```

Replace `usr_3a9f12` with the actual `question_id` from the query above, and `admin@wu.ac.at` with your email address.

#### Reject a single task

```sql
UPDATE benchmark_tasks
SET is_public = 0,
    validation_status = 'rejected',
    validated_by = 'admin@wu.ac.at'
WHERE question_id = 'usr_3a9f12';
```

#### Approve all pending user submissions at once

```sql
UPDATE benchmark_tasks
SET is_public = 1,
    validation_status = 'approved',
    validated_by = 'admin@wu.ac.at'
WHERE source = 'user_submitted'
AND validation_status = 'pending';
```

After running any query, click **Write Changes** in DB Browser to save.

> **Effect of approval:** Setting `is_public = 1` causes the task to be included in the `GET /api/leaderboard` endpoint calculations automatically. No server restart is needed — the leaderboard query reads from the database on every request.

> **Planned:** A proper `auth-pages/admin.html` page with Approve/Reject buttons will be built in a later phase. It will call the existing `POST /admin/tasks/{id}/approve` and `/reject` endpoints which are already implemented in `main.py`.

---

### Phase 5 — Real Benchmark Script

Replace `dummy_pipeline.py` with `backend/processing/pipeline.py` that:

- Reads the task from the `benchmark_tasks` table instead of an Excel file
- Calls all 10 model APIs with 3 trials each using the existing prompt templates
- Scores using the SC/MC formula for `single_choice` and `multi_choice` tasks
- Calls the LLM judge (`gpt-5-mini`) for `open_text`, `open_numeric`, and `journal_entry` tasks
- Writes results to `benchmark_runs` and `benchmark_outputs` tables
- Keeps the same function signature: `run_pipeline(submission_id: int, db: Session = None) -> None`

Then in `submissions.py`, change one import line to activate the real script:

```python
from backend.processing.pipeline import run_pipeline
```

---

### Phase 5 — Live Leaderboard

Update `public/main.js` to fetch from `GET /api/leaderboard` instead of reading from `data.js`. The endpoint is already implemented in `main.py` and returns data in the same format as the existing `lbData` array.

---

### Phase 6 — Deployment to Render

Deploy the FastAPI backend as a **Render Web Service** and the static HTML files as **Render Static Sites**. Key changes needed:

- Switch `DATABASE_URL` in `.env` to the Render PostgreSQL connection string
- Change the `API` constant in `auth-pages.js` from `http://localhost:8000` to the Render service URL
- Add the Render URL to the `ALLOWED_ORIGINS` list in `main.py`
- The JWKS fallback in `auth.py` will work automatically on Render (unrestricted internet access)
- Run `alembic upgrade head` on the Render database on first deploy

---

### Phase 7 — Stripe Payments

The database schema already includes all payment fields in the `submissions` table (`payment_status`, `stripe_payment_id`, `price_charged`). The `settings` table has `price_per_submission` for configuring the price without code changes.

Add Stripe integration between form submission and pipeline triggering:

1. After `POST /submissions/prepare`, redirect to a Stripe checkout page
2. On payment success, Stripe calls a webhook endpoint (`POST /stripe/webhook`)
3. The webhook sets `payment_status = "paid"` and triggers `run_pipeline`
4. Set `STRIPE_SECRET_KEY` and `STRIPE_WEBHOOK_SECRET` in `.env`

---

*AccountingBench Developer Documentation · Version 1.0 · April 2026*
*WU Vienna · Financial Accounting & Auditing Group · Board Service Center*
