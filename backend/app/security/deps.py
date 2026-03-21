from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, RevokedToken
from app.services.auth_access import normalize_role, user_is_active
from app.security.jwt import decode_token


@dataclass
class Principal:
    typ: str
    user_id: str | None = None
    role: str | None = None
    owner_sub: str | None = None
    anon: bool | None = None
    jti: str | None = None


def _get_request_token(request: Request) -> str | None:
    auth = request.headers.get("Authorization") or ""
    if auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1].strip()
        if token:
            return token
    cookie_token = str(request.cookies.get(settings.auth_session_cookie_name) or "").strip()
    return cookie_token or None


def _coerce_user_pk(user_id: str):
    try:
        return UUID(str(user_id))
    except ValueError:
        return user_id


def get_optional_principal(
    request: Request,
    db: Session = Depends(get_db),
) -> Principal | None:
    token = _get_request_token(request)
    if not token:
        return None

    payload = decode_token(token)
    typ = payload.get("typ")

    if typ == "user":
        user_id = payload.get("sub")
        role = normalize_role(payload.get("role"))
        jti = payload.get("jti")
        if not user_id or not role or not jti:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

        user = db.get(User, _coerce_user_pk(user_id))
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        if not user_is_active(user):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User inactive")

        revoked = db.query(RevokedToken).filter(RevokedToken.jti == jti).first()
        if revoked is not None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session revoked")

        return Principal(typ="user", user_id=str(user.id), role=normalize_role(user.role), jti=jti)

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session type")


def get_current_principal(
    principal: Principal | None = Depends(get_optional_principal),
) -> Principal:
    if principal is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return principal


def require_role(role: str):
    def _require(principal: Principal = Depends(get_current_principal)) -> Principal:
        if principal.typ != "user":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User token required")
        if normalize_role(principal.role) != normalize_role(role):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return principal

    return _require
