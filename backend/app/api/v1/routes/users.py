"""Email + password authentication: register, login, invite."""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import PasswordResetToken, User
from app.security.deps import get_current_principal, Principal
from app.security.jwt import create_user_token
from app.services.email import send_welcome, send_invite, send_password_reset

router = APIRouter(tags=["users"])


# ---------- helpers ----------
def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def _verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


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


# ---------- endpoints ----------
@router.post("/auth/register", response_model=AuthOut, status_code=201)
def register(data: RegisterIn, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu email zaten kayıtlı.")
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="Şifre en az 6 karakter olmalı.")

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
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not user.password_hash:
        raise HTTPException(status_code=401, detail="Email veya şifre hatalı.")
    if not _verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email veya şifre hatalı.")
    if user.is_suspended:
        raise HTTPException(status_code=403, detail="Hesabınız askıya alınmış.")

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
        raise HTTPException(status_code=403, detail="Sadece admin davet edebilir.")

    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Bu email zaten kayıtlı.")

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
    if user.password_hash and not _verify_password(old_pw, user.password_hash):
        raise HTTPException(status_code=401, detail="Mevcut şifre hatalı.")

    user.password_hash = _hash_password(new_pw)
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

    user.password_hash = _hash_password(data.new_password)
    prt.used_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "detail": "Şifreniz başarıyla sıfırlandı."}
