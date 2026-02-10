from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db

router = APIRouter(tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class MeOut(BaseModel):
    sub: str
    email: EmailStr


def _now():
    return datetime.now(timezone.utc)


def _sign(payload: dict, expires_delta: timedelta) -> str:
    exp = _now() + expires_delta
    to_encode = {**payload, "exp": exp}
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def create_tokens(sub: str, email: str) -> TokenPair:
    access = _sign({"sub": sub, "email": email, "type": "access"}, timedelta(minutes=settings.ACCESS_TOKEN_MINUTES))
    refresh = _sign({"sub": sub, "email": email, "type": "refresh"}, timedelta(days=settings.REFRESH_TOKEN_DAYS))
    return TokenPair(access_token=access, refresh_token=refresh)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


@router.post("/auth/login", response_model=TokenPair)
def login(data: LoginIn, db: Session = Depends(get_db)):
    raise HTTPException(status_code=501, detail="Password login not configured. Use OAuth or guest mode.")


class RefreshIn(BaseModel):
    refresh_token: str


@router.post("/auth/refresh", response_model=TokenPair)
def refresh(data: RefreshIn):
    payload = decode_token(data.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return create_tokens(sub=payload["sub"], email=payload["email"])


@router.get("/auth/me", response_model=MeOut)
def me(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid access token")
    return MeOut(sub=payload["sub"], email=payload["email"])


class GuestOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/auth/guest", response_model=GuestOut)
def guest():
    sub = str(uuid4())
    email = f"guest+{sub}@stellcodex.local"
    tokens = create_tokens(sub=sub, email=email)
    return GuestOut(access_token=tokens.access_token)
