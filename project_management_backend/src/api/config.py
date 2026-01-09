"""
Configuration module for loading environment variables and initializing services.

Key goals:
- Never crash app startup due to missing optional config (JWT_SECRET, Supabase).
- Support both backend-native env vars (SUPABASE_URL, SUPABASE_KEY, FRONTEND_URL, ...)
  and the current container's REACT_APP_* env var naming.
- Initialize Supabase lazily and handle connection errors at call time.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load environment variables from .env if present. This should never raise.
load_dotenv()


def _getenv_any(*names: str, default: Optional[str] = None) -> Optional[str]:
    """Return the first non-empty value found among env var names."""
    for name in names:
        value = os.getenv(name)
        if value is not None and str(value).strip() != "":
            return value
    return default


def _mask(value: Optional[str], show: int = 4) -> str:
    """Mask secrets for logging."""
    if not value:
        return "✗ Missing"
    s = str(value)
    if len(s) <= show:
        return "✓ Configured (masked)"
    return f"✓ Configured (masked: {s[:show]}…)"


# Environment variables (support both backend + REACT_APP_ prefixes)
SUPABASE_URL = _getenv_any("SUPABASE_URL", "REACT_APP_SUPABASE_URL")
SUPABASE_KEY = _getenv_any("SUPABASE_KEY", "REACT_APP_SUPABASE_KEY")

BACKEND_URL = _getenv_any("BACKEND_URL", "REACT_APP_BACKEND_URL", default="http://localhost:3001")
FRONTEND_URL = _getenv_any("FRONTEND_URL", "REACT_APP_FRONTEND_URL", default="http://localhost:3000")
SITE_URL = _getenv_any("SITE_URL", "REACT_APP_SITE_URL", default=FRONTEND_URL)

# CORS origins: allow explicit list, else fallback to common dev origins
ALLOWED_ORIGINS_RAW = _getenv_any("ALLOWED_ORIGINS", "REACT_APP_ALLOWED_ORIGINS", default="")
ALLOWED_ORIGINS = [o.strip() for o in ALLOWED_ORIGINS_RAW.split(",") if o.strip()]

JWT_SECRET = _getenv_any("JWT_SECRET", "REACT_APP_JWT_SECRET")
JWT_ALGORITHM = _getenv_any("JWT_ALGORITHM", "REACT_APP_JWT_ALGORITHM", default="HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(_getenv_any("ACCESS_TOKEN_EXPIRE_MINUTES", default="60") or "60")

# Track whether we consider auth "fully configured"
AUTH_CONFIGURED = bool(JWT_SECRET) or (bool(SUPABASE_URL) and bool(SUPABASE_KEY))


# Supabase client (lazy)
_supabase_client = None


# PUBLIC_INTERFACE
def get_supabase_client():
    """
    Get (lazy) Supabase client instance.

    The Supabase client is initialized on first use. If SUPABASE_URL / SUPABASE_KEY
    are missing, a ValueError is raised. Importantly: the module import itself never fails.

    Returns:
        supabase.Client: Supabase client for database and auth operations.

    Raises:
        ValueError: If Supabase credentials are not configured.
        RuntimeError: If the Supabase client cannot be created (e.g., bad install).
    """
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set to use Supabase features")

    try:
        # Import lazily to avoid hard failing application startup if dependency is missing.
        from supabase import create_client  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(f"Supabase dependency is not available: {e}") from e

    try:
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client created (lazy init) ✓")
        return _supabase_client
    except Exception as e:
        # Do not crash startup - callers can decide how to handle.
        raise RuntimeError(f"Failed to initialize Supabase client: {e}") from e


# Backwards-compatible name used throughout routers.
# Note: this is intentionally Optional-like; code should check for None or use get_supabase_client.
supabase = None
try:
    # Only set supabase eagerly if env is present AND import is available.
    # Still do not crash startup if anything goes wrong.
    if SUPABASE_URL and SUPABASE_KEY:
        supabase = get_supabase_client()
except Exception as e:
    logger.warning(f"Supabase not available at startup (degraded mode): {e}")
    supabase = None


# PUBLIC_INTERFACE
def get_env_summary() -> dict:
    """
    Return a masked summary of key env/config values for startup logs.

    Returns:
        dict: Summary of configuration status with secrets masked.
    """
    return {
        "SUPABASE_URL": _mask(SUPABASE_URL),
        "SUPABASE_KEY": _mask(SUPABASE_KEY),
        "JWT_SECRET": _mask(JWT_SECRET),
        "FRONTEND_URL": FRONTEND_URL,
        "BACKEND_URL": BACKEND_URL,
        "SITE_URL": SITE_URL,
        "ALLOWED_ORIGINS": ALLOWED_ORIGINS,
        "AUTH_CONFIGURED": AUTH_CONFIGURED,
    }
