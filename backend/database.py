"""
AccountingBench — Database Connection
=======================================
Creates the SQLAlchemy engine and session factory.
Every other file in the backend imports get_db or SessionLocal from here.

Usage in a FastAPI endpoint:
    from backend.database import get_db
    from sqlalchemy.orm import Session

    @app.get("/example")
    def example(db: Session = Depends(get_db)):
        ...

Usage in the Python pipeline script (outside a request):
    from backend.database import SessionLocal

    def run_pipeline(submission_id: int):
        db = SessionLocal()
        try:
            ...
        finally:
            db.close()
"""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.models import Base

# ── Load environment variables from .env ─────────────────────────────────────
load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. "
        "Add it to your .env file.\n"
        "  Local development:  DATABASE_URL=sqlite:///./accountingbench.db\n"
        "  Production:         DATABASE_URL=postgresql://user:password@host/dbname"
    )

# ── SQLite vs PostgreSQL ──────────────────────────────────────────────────────
# SQLite is fine for local development — no separate server needed.
# Switch to the Render PostgreSQL URL when deploying.
#
# SQLite requires connect_args={"check_same_thread": False} because FastAPI
# handles requests on multiple threads. PostgreSQL does not need this.

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False,         # Set echo=True to print every SQL statement (useful for debugging)
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True, # Reconnects automatically if the DB connection drops
        echo=False,
    )

# ── Session factory ───────────────────────────────────────────────────────────
# SessionLocal() creates a new database session.
# Use this directly in the pipeline script (outside a FastAPI request).
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ── FastAPI dependency ────────────────────────────────────────────────────────
def get_db():
    """
    Yields a database session for use in FastAPI endpoints via Depends(get_db).
    Automatically closes the session when the request finishes, even if an
    exception is raised.

    Example:
        @app.get("/users/me")
        def get_me(db: Session = Depends(get_db), user=Depends(get_current_user)):
            return db.query(User).filter_by(id=user).first()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Create all tables ─────────────────────────────────────────────────────────
def create_tables():
    """
    Creates all tables defined in models.py if they do not already exist.

    You do NOT need to call this manually — Alembic handles table creation
    via migrations (alembic upgrade head).

    This function is only useful for quick local testing before Alembic
    is set up. Do not use it in production.
    """
    Base.metadata.create_all(bind=engine)


# ── Connection health check ───────────────────────────────────────────────────
def check_connection():
    """
    Tests that the database is reachable.
    Called on server startup in main.py to catch misconfigured DATABASE_URL early.

    Returns True if connected, raises an exception if not.
    """
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True
