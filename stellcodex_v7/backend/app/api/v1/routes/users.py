"""Email + password authentication: register, login, invite."""
from __future__ import annotations

import bcrypt
import hashlib
import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import PasswordResetToken, User
from app.security.deps import get_current_principal, Principal
from app.security.jwt import create_user_token
from app.services.email import email_delivery_enabled, send_invite, send_password_reset, send_welcome

router = APIRouter(tags=["users"])


# ---------- helpers ----------
def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def _hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _issue_password_reset_token(db: Session, user: User) -> str:
    raw_token = secrets.token_urlsafe(32)
    reset_token = PasswordResetToken(
        user_id=user.id,
        token_hash=_hash_reset_token(raw_token),
        expires_at=datetime.utcnow() + timedelta(hours=1),
    )
    db.add(reset_token)
    db.commit()
    return raw_token


# ---------- schemas ----------
class RegisterIn(BaseModel):
    email: EmailStr
    password: str


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class AuthOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: str


class InviteIn(BaseModel):
    email: EmailStr
    role: str = "user"
    password: str | None = None


class PasswordResetRequestIn(BaseModel):
    email: EmailStr


class PasswordResetRequestOut(BaseModel):
    ok: bool = True
    delivery_enabled: bool


class PasswordResetIn(BaseModel):
    token: str
    password: str


class PasswordResetOut(BaseModel):
    ok: bool = True


# ---------- endpoints ----------
@router.post("/auth/register", response_model=AuthOut, status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    existing = db.query(User).filter_by(email=data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="This email is already registered.")
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long.")

    user = User(
        email=data.email,
        password_hash=_hash_password(data.password),
        role="user",
        is_suspended=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_user_token(str(user.id), user.role)
    try:
        send_welcome(user.email)
    except Exception:
        pass
    return AuthOut(
        access_token=token,
        user_id=str(user.id),
        email=user.email,
        role=user.role,
    )


@router.post("/auth/login", response_model=AuthOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=data.email).first()
    if not user or not user.password_hash:
        raise HTTPException(status_code=401, detail="Email or password is invalid.")
    if not _verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email or password is invalid.")
    if user.is_suspended:
        raise HTTPException(status_code=403, detail="Your account is suspended.")

    token = create_user_token(str(user.id), user.role)
    return AuthOut(
        access_token=token,
        user_id=str(user.id),
        email=user.email,
        role=user.role,
    )


@router.post("/auth/invite", response_model=AuthOut, status_code=201)
def invite_user(
    data: InviteIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    """Admin can invite/create users with a specific role."""
    if principal.typ != "user" or principal.role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can invite users.")

    existing = db.query(User).filter_by(email=data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="This email is already registered.")

    password = data.password or _generate_temp_password()
    user = User(
        email=data.email,
        password_hash=_hash_password(password),
        role=data.role,
        is_suspended=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_user_token(str(user.id), user.role)
    try:
        send_invite(user.email, password)
    except Exception:
        pass
    return AuthOut(
        access_token=token,
        user_id=str(user.id),
        email=user.email,
        role=user.role,
    )


@router.post("/auth/request-password-reset", response_model=PasswordResetRequestOut)
def request_password_reset(data: PasswordResetRequestIn, db: Session = Depends(get_db)):
    delivery_enabled = email_delivery_enabled()
    user = db.query(User).filter_by(email=data.email).first()
    if not delivery_enabled or not user or not user.password_hash or user.is_suspended:
        return PasswordResetRequestOut(delivery_enabled=delivery_enabled)

    reset_token = _issue_password_reset_token(db, user)
    try:
        send_password_reset(user.email, reset_token)
    except Exception:
        pass
    return PasswordResetRequestOut(delivery_enabled=delivery_enabled)


@router.post("/auth/reset-password", response_model=PasswordResetOut)
def reset_password(data: PasswordResetIn, db: Session = Depends(get_db)):
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters long.")

    token_hash = _hash_reset_token(data.token.strip())
    reset_token = db.query(PasswordResetToken).filter_by(token_hash=token_hash).first()
    now = datetime.utcnow()
    if not reset_token or reset_token.used_at is not None or reset_token.expires_at <= now:
        raise HTTPException(status_code=400, detail="Reset token is invalid or expired.")

    user = db.get(User, reset_token.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User was not found.")
    if user.is_suspended:
        raise HTTPException(status_code=403, detail="Your account is suspended.")

    user.password_hash = _hash_password(data.password)
    reset_token.used_at = now
    db.commit()
    return PasswordResetOut()


@router.put("/auth/change-password")
def change_password(
    data: dict,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    if principal.typ != "user" or not principal.user_id:
        raise HTTPException(status_code=401, detail="No active session was found.")
    old_pw = data.get("old_password", "")
    new_pw = data.get("new_password", "")
    if len(new_pw) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters long.")

    user = db.get(User, principal.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User was not found.")
    if user.password_hash and not _verify_password(old_pw, user.password_hash):
        raise HTTPException(status_code=401, detail="Current password is invalid.")

    user.password_hash = _hash_password(new_pw)
    db.commit()
    return {"ok": True}


def _generate_temp_password() -> str:
    import secrets, string
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(12))
