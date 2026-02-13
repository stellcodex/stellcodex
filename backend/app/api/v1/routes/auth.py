from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter
from pydantic import BaseModel

from app.security.jwt import create_guest_token

router = APIRouter(tags=["auth"])


class GuestOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    owner_sub: str


@router.post("/auth/guest", response_model=GuestOut)
def guest():
    owner_sub = str(uuid4())
    token = create_guest_token(owner_sub=owner_sub, anon=True)
    return GuestOut(access_token=token, owner_sub=owner_sub)
