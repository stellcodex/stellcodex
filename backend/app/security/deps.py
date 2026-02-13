from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User, RevokedToken
from app.security.jwt import decode_token


@dataclass
class Principal:
    typ: str
    user_id: str | None = None
    role: str | None = None
    owner_sub: str | None = None
    anon: bool | None = None
    jti: str | None = None


def _get_bearer_token(request: Request) -> str:
    auth = request.headers.get("Authorization") or ""
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    token = auth.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    return token


def get_current_principal(
    request: Request,
    db: Session = Depends(get_db),
) -> Principal:
    token = _get_bearer_token(request)
    payload = decode_token(token)
    typ = payload.get("typ")

    if typ == "guest":
        owner_sub = payload.get("owner_sub")
        if not owner_sub:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid guest token")
        return Principal(typ="guest", owner_sub=str(owner_sub), anon=bool(payload.get("anon", True)))

    if typ == "user":
        user_id = payload.get("sub")
        role = payload.get("role")
        jti = payload.get("jti")
        if not user_id or not role or not jti:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user token")

        user = db.get(User, user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        if user.is_suspended:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User suspended")

        revoked = db.query(RevokedToken).filter(RevokedToken.jti == jti).first()
        if revoked is not None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")

        return Principal(typ="user", user_id=str(user.id), role=user.role, jti=jti)

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")


def require_role(role: str):
    def _require(principal: Principal = Depends(get_current_principal)) -> Principal:
        if principal.typ != "user":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User token required")
        if principal.role != role:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")
        return principal

    return _require
