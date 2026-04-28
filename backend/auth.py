"""
AccountingBench — Authentication
==================================
Handles two things:
  1. Verifying the Clerk JWT session token on every protected request.
  2. Checking the user's email domain against the allowed_domains table.

Token verification strategy:
  - LOCAL first:   Uses CLERK_PEM_PUBLIC_KEY from .env — fast, no network call.
                   Works even on machines with restricted internet access.
  - JWKS fallback: If the local key fails or is not set, fetches Clerk's
                   public keys from the internet. This handles automatic key
                   rotation and works on production servers (e.g. Render).

.env variables needed:
  CLERK_PEM_PUBLIC_KEY   — the RSA public key from Clerk dashboard (local dev)
  CLERK_JWKS_URL         — your Clerk JWKS URL (production / fallback)
  CLERK_PUBLISHABLE_KEY  — used to derive the JWKS URL if CLERK_JWKS_URL not set
  ADMIN_EMAIL            — your own email address for admin access

Usage in a FastAPI endpoint:
    from backend.auth import get_current_user, require_admin

    @app.get("/submissions/mine")
    def my_submissions(user_id: str = Depends(get_current_user), db = Depends(get_db)):
        ...

    @app.post("/admin/tasks/{task_id}/approve")
    def approve(task_id: int, admin_id: str = Depends(require_admin), db = Depends(get_db)):
        ...
"""

import logging
import os
from functools import lru_cache

import jwt as pyjwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import AllowedDomain, User

#load_dotenv()
from pathlib import Path
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_PATH, override=False)


logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────
CLERK_PEM_PUBLIC_KEY  = os.environ.get("CLERK_PEM_PUBLIC_KEY",  "")
CLERK_PUBLISHABLE_KEY = os.environ.get("CLERK_PUBLISHABLE_KEY", "")
CLERK_JWKS_URL        = os.environ.get("CLERK_JWKS_URL",        "")
ADMIN_EMAIL           = os.environ.get("ADMIN_EMAIL",           "")

if not ADMIN_EMAIL:
    raise RuntimeError(
        "ADMIN_EMAIL is not set in your .env file. "
        "Set it to your own email address."
    )


# ── Derive JWKS URL from publishable key (if not set directly) ────────────────
def _derive_jwks_url() -> str:
    """
    Derives the Clerk JWKS URL from the publishable key.
    The publishable key is base64-encoded and contains the frontend API host.
    Example: pk_test_Y2xlcmsuZXhhbXBsZS5jb20k
      → decodes to → clerk.example.com
      → JWKS URL   → https://clerk.example.com/.well-known/jwks.json
    """
    if not CLERK_PUBLISHABLE_KEY:
        return ""
    try:
        import base64
        raw    = CLERK_PUBLISHABLE_KEY.split("_", 2)[-1]
        padded = raw + "=" * (-len(raw) % 4)
        host   = base64.b64decode(padded).decode("utf-8").rstrip("$")
        return f"https://{host}/.well-known/jwks.json"
    except Exception:
        return ""


def _get_jwks_url() -> str:
    """Returns the JWKS URL — from .env directly, or derived from publishable key."""
    return CLERK_JWKS_URL or _derive_jwks_url()


# ── JWKS client (cached — fetched at most once per server start) ──────────────
@lru_cache(maxsize=1)
def _get_jwks_client():
    """
    Creates a PyJWKClient that fetches and caches Clerk's public keys.
    Only used as a fallback when the local PEM key is not available or fails.
    Requires internet access.
    """
    from jwt import PyJWKClient
    jwks_url = _get_jwks_url()
    if not jwks_url:
        return None
    logger.info(f"Clerk JWKS URL: {jwks_url}")
    return PyJWKClient(jwks_url, cache_keys=True)


# ── Core token verification ───────────────────────────────────────────────────
def _verify_clerk_token(token: str) -> dict:
    """
    Verifies a Clerk JWT and returns its claims dict.

    Strategy:
      1. Try the local PEM public key first (fast, no network).
      2. If that fails or the key is not set, fall back to JWKS (requires internet).

    Returns a dict containing at minimum:
        sub   — Clerk user ID, e.g. "user_2abc..."
        email — the user's primary email address

    Raises HTTPException(401) if the token is invalid or expired.
    """
    last_error = None

    # ── STEP 1: Try local PEM key ─────────────────────────────────────────────
    if CLERK_PEM_PUBLIC_KEY:
        try:
            claims = pyjwt.decode(
                token,
                CLERK_PEM_PUBLIC_KEY,
                algorithms=["RS256"],
                options={"verify_exp": True},
            )
            return claims  # ✓ verified locally

        except pyjwt.ExpiredSignatureError:
            # Token is definitely expired — no point trying JWKS
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Session has expired. Please sign in again.",
            )
        except pyjwt.InvalidTokenError as e:
            # Could be a key rotation issue — fall through to JWKS
            last_error = e
            logger.debug(f"Local PEM verification failed (trying JWKS): {e}")

    # ── STEP 2: Fall back to JWKS ─────────────────────────────────────────────
    try:
        client = _get_jwks_client()
        if client is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=(
                    "Authentication is not configured. "
                    "Set CLERK_PEM_PUBLIC_KEY or CLERK_JWKS_URL in your .env file."
                ),
            )

        signing_key = client.get_signing_key_from_jwt(token)
        claims = pyjwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_exp": True},
        )
        return claims  # ✓ verified via JWKS

    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session has expired. Please sign in again.",
        )
    except pyjwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid session token.",
        )
    except HTTPException:
        raise  # re-raise our own HTTP exceptions unchanged
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not verify session. Please sign in again.",
        )


# ── Extract token from request ────────────────────────────────────────────────
def _get_token_from_request(request: Request) -> str:
    """
    Extracts the Clerk session token from the request.

    Checks in this order:
      1. __session cookie  — set automatically by Clerk's JS SDK
      2. Authorization: Bearer header  — used when calling the API directly
         (e.g. from fetch() with a manually attached token, or API testing tools)
    """
    # Cookie (set by Clerk's JS SDK automatically)
    token = request.cookies.get("__session")
    if token:
        return token

    # Authorization header (fetch() calls from the frontend JS)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1]

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not signed in. Please sign in to continue.",
    )


# ── Domain check ──────────────────────────────────────────────────────────────
def _check_domain(email: str, db: Session) -> None:
    """
    Checks that the email domain is in the allowed_domains table.
    This replaces the Clerk Allowlist premium feature.

    Raises HTTPException(403) if the domain is not on the list.
    Add domains via the admin interface or directly in the database.
    """
    if not email or "@" not in email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid email address on account.",
        )

    domain  = email.split("@")[1].lower().strip()
    allowed = db.query(AllowedDomain).filter_by(domain=domain).first()

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Your email domain (@{domain}) is not authorised to access "
                "this service. Please contact the administrator."
            ),
        )


# ── Upsert user in local database ────────────────────────────────────────────
def _upsert_user(user_id: str, email: str, claims: dict, db: Session) -> None:
    """
    Creates or updates the user record in the local database on every login.
    Fast in practice — only writes if something has changed.
    """
    from datetime import datetime

    user = db.query(User).filter_by(id=user_id).first()

    if user is None:
        # First login — create the user
        user = User(
            id         = user_id,
            email      = email,
            first_name = claims.get("first_name") or claims.get("given_name"),
            last_name  = claims.get("last_name")  or claims.get("family_name"),
            created_at = datetime.now(),
        )
        db.add(user)
        db.commit()
        logger.info(f"New user created in database: {email}")

    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has been deactivated. Please contact the administrator.",
        )


# ── FastAPI dependencies ──────────────────────────────────────────────────────

async def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> str:
    """
    FastAPI dependency — verifies the Clerk session and checks the domain.

    Returns the Clerk user ID string if everything is valid.
    Raises HTTPException(401) if not signed in or token is invalid.
    Raises HTTPException(403) if the email domain is not allowed.

    Add to any endpoint that requires a logged-in user:
        @app.get("/protected")
        def my_route(user_id: str = Depends(get_current_user)):
            ...
    """
    token  = _get_token_from_request(request)
    claims = _verify_clerk_token(token)

    user_id = claims.get("sub", "")
    # Clerk puts the email in different fields depending on the token version
    email = (
        claims.get("email")
        or claims.get("primary_email_address")
        or ""
    )

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID.",
        )

    if not email:
        logger.warning(
            f"Token for user {user_id} has no email claim. "
            "Check Clerk JWT template settings — email must be included."
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Your token does not include an email address. "
                "Please sign out and sign in again."
            ),
        )

    # Check the domain is allowed
    _check_domain(email, db)

    # Create or update the user record
    _upsert_user(user_id, email, claims, db)

    return user_id


async def require_admin(
    request: Request,
    db: Session = Depends(get_db),
) -> str:
    """
    FastAPI dependency — same as get_current_user but also checks that
    the signed-in user's email matches ADMIN_EMAIL in .env.

    Raises HTTPException(403) if the user is not the admin.

    Add to any admin-only endpoint:
        @app.post("/admin/tasks/{task_id}/approve")
        def approve(task_id: int, admin_id: str = Depends(require_admin)):
            ...
    """
    user_id = await get_current_user(request, db)

    user = db.query(User).filter_by(id=user_id).first()
    if not user or user.email.lower() != ADMIN_EMAIL.lower():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )

    return user_id


async def get_optional_user(
    request: Request,
    db: Session = Depends(get_db),
) -> str | None:
    """
    FastAPI dependency — like get_current_user but returns None instead of
    raising an error if the user is not signed in.

    Useful for public endpoints that show extra data when logged in:
        @app.get("/api/leaderboard")
        def leaderboard(user_id: str | None = Depends(get_optional_user)):
            ...
    """
    try:
        return await get_current_user(request, db)
    except HTTPException:
        return None
