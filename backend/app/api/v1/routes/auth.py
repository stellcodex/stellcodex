from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Cookie, Header, Request, Response
from pydantic import BaseModel

from app.security.jwt import create_guest_token

router = APIRouter(tags=["auth"])


class GuestOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    guest_id: str
    owner_sub: str


def _normalize_guest_id(value: str | None) -> str | None:
    if value is None:
        return None
    guest_id = value.strip()
    if not guest_id:
        return None
    if guest_id.startswith("guest:"):
        guest_id = guest_id.split(":", 1)[1].strip()
    return guest_id or None


@router.post("/auth/guest", response_model=GuestOut)
def guest(
    request: Request,
    response: Response,
    x_guest_id: str | None = Header(default=None, alias="X-Guest-Id"),
    stell_guest_id: str | None = Cookie(default=None),
):
    guest_id = _normalize_guest_id(x_guest_id) or _normalize_guest_id(stell_guest_id)
    if not guest_id:
        guest_id = str(uuid4())

    token = create_guest_token(owner_sub=guest_id, anon=True)

    response.set_cookie(
        key="stell_guest_id",
        value=guest_id,
        max_age=60 * 60 * 24 * 365,
        httponly=True,
        samesite="lax",
        path="/",
        secure=request.url.scheme == "https",
    )

    return GuestOut(access_token=token, guest_id=guest_id, owner_sub=guest_id)
