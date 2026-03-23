from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import HTTPException, Response, status
from jose import JWTError, jwt

from app.core.config import settings


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_user_token(user_id: str, role: str, ttl_minutes: int | None = None) -> str:
    effective_ttl = ttl_minutes or settings.auth_session_ttl_minutes
    exp = _now() + timedelta(minutes=effective_ttl)
    payload = {
        "typ": "user",
        "sub": user_id,
        "role": role,
        "jti": str(uuid4()),
        "exp": exp,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def create_oauth_state_token(redirect_to: str, ttl_minutes: int | None = None) -> str:
    exp = _now() + timedelta(minutes=ttl_minutes or settings.auth_google_state_ttl_minutes)
    payload = {
        "typ": "oauth_state",
        "redirect_to": redirect_to,
        "nonce": str(uuid4()),
        "exp": exp,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def set_session_cookie(response: Response, token: str, *, secure: bool) -> None:
    response.set_cookie(
        key=settings.auth_session_cookie_name,
        value=token,
        max_age=settings.auth_session_ttl_minutes * 60,
        httponly=True,
        samesite="lax",
        path="/",
        secure=secure,
    )


def clear_session_cookie(response: Response, *, secure: bool) -> None:
    response.delete_cookie(
        key=settings.auth_session_cookie_name,
        httponly=True,
        samesite="lax",
        path="/",
        secure=secure,
    )


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
