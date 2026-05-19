# Changelog

All versions correspond to branches on [GitHub](https://github.com/mkaburek-wu/AccountingBench).

---

## V6.0 — `4880fe9` · May 2026
- Admin panel (`admin.html`): task review, user management, live KPI stats, domain management
- Nav bar buttons (Account Settings, Sign Out, Admin Panel) on all auth pages
- Logo on all auth pages links back to My Submissions
- `backend/admin.py`: `/admin/stats`, `/admin/users`, activate/deactivate endpoints
- `/me` endpoint returns `is_admin` flag; account page added to all auth nav bars

## V5.0 — `90e8c6b`
- Stripe Checkout payment flow (session creation, polling, redirect, confirmation)
- `payment-success.html` added for post-payment pipeline trigger
- JavaScript moved from inline HTML to dedicated `.js` files
- Mobile bottom tab bar added to all auth pages
- Account deletion (`account.html`): removes DB records then calls Clerk API
- Deployment files added (`requirements.txt`, `_redirects`) for Render
- Data layer fixes: hardcoded values removed, all scores linked to `results.js`

## V4.1 — `a4e02c8`
- IFRS regulatory framework results added
- Bug fixes and small UI text changes

## V4.0 — `480300a`
- Benchmark results updated across multiple models
- `results.js` / `data.js` data layer introduced (all values configurable)
- `rerun_model.py` added for running new models on existing DB tasks
- Team member (Daniel Höllmüller) added

## V3.0 — `3926573`
- Sign-in, upload, and results pages fully working end-to-end
- SQLite database with SQLAlchemy + Alembic migrations
- FastAPI backend with Clerk JWT authentication and domain restriction
- Real benchmark pipeline (`pipeline.py`) with parallel model execution

## V2.0 — `eaadd04`
- General website improvements and structure cleanup

## V1.0 — `84f6a6f`
- Initial upload: public site static pages, basic project structure
