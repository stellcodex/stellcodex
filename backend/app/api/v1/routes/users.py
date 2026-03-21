"""Email + password authentication: register, login, invite."""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import PasswordResetToken, User
from app.security.deps import get_current_principal, Principal
from app.security.jwt import create_user_token, set_session_cookie
from app.services.auth_access import (
    hash_password,
    normalize_email,
    normalize_role,
    serialize_session,
    set_user_active,
    touch_last_login,
    user_is_active,
    verify_password,
)
from app.services.email import send_welcome, send_invite, send_password_reset

router = APIRouter(tags=["users"])


# ---------- schemas ----------
class RegisterIn(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class AuthOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: str
    full_name: str | None = None
    auth_provider: str
    session: dict


class InviteIn(BaseModel):
    email: EmailStr
    role: str = "member"
    password: str | None = None
    full_name: str | None = None


def _is_secure_request(request: Request) -> bool:
    forwarded_proto = str(request.headers.get("x-forwarded-proto") or "").strip().lower()
    if forwarded_proto:
        return forwarded_proto == "https"
    return request.url.scheme == "https"


# ---------- endpoints ----------
@router.post("/auth/register", response_model=AuthOut, status_code=201)
def register(data: RegisterIn, request: Request, response: Response, db: Session = Depends(get_db)):
    normalized_email = normalize_email(data.email)
    existing = db.query(User).filter(User.email == normalized_email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu email zaten kayıtlı.")
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="Şifre en az 6 karakter olmalı.")

    user = User(
        email=normalized_email,
        full_name=(data.full_name or "").strip() or None,
        password_hash=hash_password(data.password),
        role="member",
        auth_provider="local",
    )
    set_user_active(user, True)
    db.add(user)
    db.commit()
    db.refresh(user)

    touch_last_login(user)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_user_token(str(user.id), user.role, ttl_minutes=settings.auth_session_ttl_minutes)
    set_session_cookie(response, token, secure=_is_secure_request(request))
    try:
        send_welcome(user.email)
    except Exception:
        pass
    return AuthOut(
        access_token=token,
        user_id=str(user.id),
        email=user.email,
        role=normalize_role(user.role),
        full_name=user.full_name,
        auth_provider=user.auth_provider,
        session=serialize_session(user),
    )


@router.post("/auth/login", response_model=AuthOut)
def login(data: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    normalized_email = normalize_email(data.email)
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user or not user.password_hash:
        raise HTTPException(status_code=401, detail="Email veya şifre hatalı.")
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email veya şifre hatalı.")
    if not user_is_active(user):
        raise HTTPException(status_code=403, detail="Hesabınız askıya alınmış.")

    touch_last_login(user)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_user_token(str(user.id), user.role, ttl_minutes=settings.auth_session_ttl_minutes)
    set_session_cookie(response, token, secure=_is_secure_request(request))
    return AuthOut(
        access_token=token,
        user_id=str(user.id),
        email=user.email,
        role=normalize_role(user.role),
        full_name=user.full_name,
        auth_provider=user.auth_provider,
        session=serialize_session(user),
    )


@router.post("/auth/invite", response_model=AuthOut, status_code=201)
def invite_user(
    data: InviteIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    """Admin can invite/create users with a specific role."""
    if principal.typ != "user" or principal.role != "admin":
        raise HTTPException(status_code=403, detail="Sadece admin davet edebilir.")

    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu email zaten kayıtlı.")

    password = data.password or _generate_temp_password()
    user = User(
        email=normalize_email(data.email),
        full_name=(data.full_name or "").strip() or None,
        password_hash=hash_password(password),
        role=normalize_role(data.role),
        auth_provider="local",
    )
    set_user_active(user, True)
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
        role=normalize_role(user.role),
        full_name=user.full_name,
        auth_provider=user.auth_provider,
        session=serialize_session(user),
    )


@router.put("/auth/change-password")
def change_password(
    data: dict,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    if principal.typ != "user" or not principal.user_id:
        raise HTTPException(status_code=401, detail="Oturum açık değil.")
    old_pw = data.get("old_password", "")
    new_pw = data.get("new_password", "")
    if len(new_pw) < 6:
        raise HTTPException(status_code=400, detail="Yeni şifre en az 6 karakter olmalı.")

    user = db.get(User, principal.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Kullanıcı bulunamadı.")
    if user.password_hash and not verify_password(old_pw, user.password_hash):
        raise HTTPException(status_code=401, detail="Mevcut şifre hatalı.")

    user.password_hash = hash_password(new_pw)
    db.commit()
    return {"ok": True}


def _generate_temp_password() -> str:
    import string
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(12))


# ---------- password reset ----------
class ForgotPasswordIn(BaseModel):
    email: EmailStr


class ResetPasswordIn(BaseModel):
    token: str
    new_password: str


@router.post("/auth/forgot-password", status_code=200)
def forgot_password(data: ForgotPasswordIn, db: Session = Depends(get_db)):
    """Token üretir ve email ile gönderir. Kullanıcı yoksa da 200 döner (enumeration koruması)."""
    user = db.query(User).filter(User.email == data.email).first()
    if user:
        token = secrets.token_urlsafe(32)
        token_hash = secrets.token_hex(32)  # store a hash, send the raw token
        import hashlib
        token_hash = hashlib.sha256(token.encode()).hexdigest()[:64]
        prt = PasswordResetToken(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=datetime.utcnow() + timedelta(hours=1),
        )
        db.add(prt)
        db.commit()
        try:
            send_password_reset(user.email, token)
        except Exception:
            pass
    return {"ok": True, "detail": "Şifre sıfırlama linki email adresinize gönderildi."}


@router.post("/auth/reset-password", status_code=200)
def reset_password(data: ResetPasswordIn, db: Session = Depends(get_db)):
    import hashlib
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Şifre en az 6 karakter olmalı.")

    token_hash = hashlib.sha256(data.token.encode()).hexdigest()[:64]
    prt = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.used_at.is_(None),
    ).first()
    if not prt:
        raise HTTPException(status_code=400, detail="Geçersiz veya kullanılmış token.")
    if prt.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Token süresi dolmuş.")

    user = db.get(User, prt.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="Kullanıcı bulunamadı.")

    user.password_hash = hash_password(data.new_password)
    prt.used_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "detail": "Şifreniz başarıyla sıfırlandı."}
