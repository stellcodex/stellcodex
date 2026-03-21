from __future__ import annotations

from datetime import datetime, timezone

import bcrypt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import RevokedToken, User
from app.security.jwt import decode_token

VALID_ROLES = {"admin", "member"}
VALID_AUTH_PROVIDERS = {"google", "local"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_email(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    return normalized or None


def normalize_role(value: str | None) -> str:
    role = str(value or "").strip().lower()
    if role in {"admin"}:
        return "admin"
    if role in {"member", "user"}:
        return "member"
    return "member"


def normalize_auth_provider(value: str | None) -> str:
    provider = str(value or "").strip().lower()
    if provider in VALID_AUTH_PROVIDERS:
        return provider
    return "local"


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def set_user_active(user: User, is_active: bool) -> None:
    user.is_active = bool(is_active)
    user.is_suspended = not bool(is_active)


def user_is_active(user: User) -> bool:
    return bool(getattr(user, "is_active", True)) and not bool(getattr(user, "is_suspended", False))


def serialize_user(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": normalize_role(user.role),
        "auth_provider": normalize_auth_provider(user.auth_provider),
        "is_active": user_is_active(user),
        "created_at": user.created_at,
        "last_login_at": user.last_login_at,
    }


def serialize_session(user: User | None) -> dict:
    payload = serialize_user(user) if user is not None else None
    return {
        "authenticated": user is not None,
        "role": payload["role"] if payload is not None else None,
        "user": payload,
    }


def is_google_admin_email(email: str | None) -> bool:
    normalized = normalize_email(email)
    return bool(normalized and normalized in settings.google_admin_whitelist)


def touch_last_login(user: User) -> None:
    user.last_login_at = _now()


def revoke_token(db: Session, token: str | None, reason: str = "logout") -> bool:
    if not token:
        return False
    try:
        payload = decode_token(token)
    except Exception:
        return False
    if payload.get("typ") != "user":
        return False
    jti = str(payload.get("jti") or "").strip()
    if not jti:
        return False
    existing = db.query(RevokedToken).filter(RevokedToken.jti == jti).first()
    if existing is not None:
        return False
    db.add(RevokedToken(jti=jti, revoked_at=_now(), reason=reason))
    db.commit()
    return True


def ensure_seed_user(
    db: Session,
    *,
    email: str | None,
    password: str | None,
    full_name: str | None,
    role: str,
) -> User | None:
    normalized_email = normalize_email(email)
    if not normalized_email or not password:
        return None

    normalized_role = normalize_role(role)
    user = db.query(User).filter(User.email == normalized_email).first()
    password_hash = hash_password(password)
    if user is None:
        user = User(
            email=normalized_email,
            full_name=(full_name or "").strip() or None,
            role=normalized_role,
            auth_provider="local",
            password_hash=password_hash,
            google_sub=None,
            created_at=_now(),
        )
        set_user_active(user, True)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    user.email = normalized_email
    user.full_name = (full_name or user.full_name or "").strip() or None
    user.role = normalized_role
    user.auth_provider = "local"
    user.password_hash = password_hash
    user.google_sub = user.google_sub or None
    set_user_active(user, True)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def ensure_seed_users(db: Session) -> None:
    ensure_seed_user(
        db,
        email=settings.auth_seed_admin_email,
        password=settings.auth_seed_admin_password,
        full_name=settings.auth_seed_admin_full_name,
        role="admin",
    )
    ensure_seed_user(
        db,
        email=settings.auth_seed_member_email,
        password=settings.auth_seed_member_password,
        full_name=settings.auth_seed_member_full_name,
        role="member",
    )


def upsert_google_user(
    db: Session,
    *,
    email: str,
    google_sub: str,
    full_name: str | None,
) -> User:
    normalized_email = normalize_email(email)
    normalized_sub = str(google_sub or "").strip()
    if not normalized_email or not normalized_sub:
        raise ValueError("Google email and sub are required")

    user = db.query(User).filter(User.google_sub == normalized_sub).first()
    if user is None:
        user = db.query(User).filter(User.email == normalized_email).first()

    target_role = "admin" if is_google_admin_email(normalized_email) else "member"
    if user is None:
        user = User(
            email=normalized_email,
            full_name=(full_name or "").strip() or None,
            role=target_role,
            auth_provider="google",
            password_hash=None,
            google_sub=normalized_sub,
            created_at=_now(),
        )
        set_user_active(user, True)
        touch_last_login(user)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    user.email = normalized_email
    if full_name and not user.full_name:
        user.full_name = full_name.strip() or None
    user.google_sub = normalized_sub
    user.auth_provider = "google"
    user.role = "admin" if is_google_admin_email(normalized_email) or normalize_role(user.role) == "admin" else "member"
    set_user_active(user, True)
    touch_last_login(user)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
