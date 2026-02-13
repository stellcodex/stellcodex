from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.core.config import settings


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_guest_token(owner_sub: str, anon: bool = True, ttl_minutes: int = 24 * 60) -> str:
    exp = _now() + timedelta(minutes=ttl_minutes)
    payload = {"typ": "guest", "owner_sub": owner_sub, "anon": anon, "exp": exp}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def create_user_token(user_id: str, role: str, ttl_minutes: int = 7 * 24 * 60) -> str:
    exp = _now() + timedelta(minutes=ttl_minutes)
    payload = {
        "typ": "user",
        "sub": user_id,
        "role": role,
        "jti": str(uuid4()),
        "exp": exp,
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
