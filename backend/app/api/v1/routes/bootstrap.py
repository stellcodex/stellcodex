from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

router = APIRouter(tags=["bootstrap"])


class BootstrapIn(BaseModel):
    email: EmailStr | None = None


@router.post("/bootstrap/admin")
def bootstrap_admin(
    request: Request,
    data: BootstrapIn | None = None,
    db: Session = Depends(get_db),
):
    token = request.headers.get("X-Bootstrap-Token") or ""
    expected = settings.bootstrap_admin_token
    if not expected:
        raise HTTPException(status_code=503, detail="Bootstrap token not configured")
    if token != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")

    existing_admin = db.query(User).filter(User.role == "admin").first()
    if existing_admin is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Admin already exists")

    email = (data.email if data else None) or settings.bootstrap_admin_email
    if not email:
        raise HTTPException(status_code=400, detail="Admin email required")

    user = User(email=email, role="admin", is_suspended=False)
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": str(user.id), "email": user.email, "role": user.role, "is_suspended": user.is_suspended}
