"""
Authentication middleware for protecting routes.

This module is intentionally resilient:
- If Supabase is not configured/available, Supabase-based auth is skipped.
- If JWT_SECRET is missing, JWT verification is disabled (unless Supabase auth works).
- In degraded mode, protected endpoints return 503 instead of crashing app startup.
"""
from __future__ import annotations

from typing import Optional

import jwt
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.api.config import JWT_ALGORITHM, JWT_SECRET, get_supabase_client

security = HTTPBearer()


def _supabase_get_user(token: str) -> Optional[dict]:
    """Try to validate token using Supabase auth; return minimal user dict if valid."""
    try:
        client = get_supabase_client()
    except Exception:
        return None

    try:
        response = client.auth.get_user(token)
        if response and getattr(response, "user", None):
            return {
                "id": response.user.id,
                "email": response.user.email,
                "user_metadata": response.user.user_metadata,
            }
    except Exception:
        return None

    return None


# PUBLIC_INTERFACE
async def get_current_user(credentials: HTTPAuthorizationCredentials) -> dict:
    """
    Get current user from the provided bearer token.

    Auth strategy:
    1) Try Supabase token verification (if configured).
    2) Fallback to local JWT verification (only if JWT_SECRET is configured).

    Args:
        credentials: HTTP authorization credentials containing the JWT token.

    Returns:
        dict: User information extracted from token.

    Raises:
        HTTPException: If auth is not configured, token invalid, or user not found.
    """
    token = credentials.credentials

    # 1) Supabase verification (preferred)
    supa_user = _supabase_get_user(token)
    if supa_user:
        return supa_user

    # 2) Local JWT verification (optional)
    if not JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication is not configured (JWT_SECRET missing and Supabase unavailable).",
        )

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"id": user_id, "email": payload.get("email")}
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


# PUBLIC_INTERFACE
def verify_token(token: str) -> Optional[dict]:
    """
    Verify JWT token and return payload.

    Notes:
    - This only verifies locally signed JWTs. If JWT_SECRET is missing, returns None.
    - Supabase token verification is done via get_current_user.

    Args:
        token: JWT token string.

    Returns:
        Optional[dict]: Token payload if valid, None otherwise.
    """
    if not JWT_SECRET:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
