from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User
from app.security.deps import get_current_principal, Principal

router = APIRouter()


@router.get("/me")
def me(
    principal: Principal = Depends(get_current_principal),
    db: Session = Depends(get_db),
):
    if principal.typ != "user" or not principal.user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User token required")
    user = db.get(User, principal.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role,
        "is_suspended": user.is_suspended,
    }
