from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.security.deps import get_optional_principal, Principal
from app.services.auth_access import serialize_session

router = APIRouter()


def _coerce_user_pk(user_id: str):
    try:
        return UUID(str(user_id))
    except ValueError:
        return user_id


@router.get("/me")
def me(
    principal: Principal | None = Depends(get_optional_principal),
    db: Session = Depends(get_db),
):
    if principal is None or principal.typ != "user" or not principal.user_id:
        return serialize_session(None)
    user = db.get(User, _coerce_user_pk(principal.user_id))
    return serialize_session(user)
