from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.core.config import settings


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _normalize_guest_id(owner_sub: str) -> str:
    guest_id = (owner_sub or "").strip()
    if guest_id.startswith("guest:"):
        guest_id = guest_id.split(":", 1)[1].strip()
    if not guest_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid guest id")
    return guest_id


def create_guest_token(owner_sub: str, anon: bool = True, ttl_minutes: int = 24 * 60) -> str:
    exp = _now() + timedelta(minutes=ttl_minutes)
    guest_id = _normalize_guest_id(owner_sub)
    payload = {
        "typ": "guest",
        "sub": f"guest:{guest_id}",
        "owner_sub": guest_id,
        "anon": anon,
        "exp": exp,
    }
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
