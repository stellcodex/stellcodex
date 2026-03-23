from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.file import UploadFile
from app.security.deps import Principal, get_current_principal
from app.services.audit import log_event

router = APIRouter()


class OwnershipClaimIn(BaseModel):
    owner_sub: str | None = None
    file_ids: List[str] | None = None


@router.post("/ownership/claim")
def claim_ownership(
    data: OwnershipClaimIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    if principal.typ != "user" or not principal.user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User token required")

    owner_sub = data.owner_sub
    if not owner_sub:
        raise HTTPException(status_code=400, detail="owner_sub required")

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

    q = db.query(UploadFile).filter(
        UploadFile.is_anonymous.is_(True),
        UploadFile.owner_user_id.is_(None),
        UploadFile.created_at >= cutoff,
        (UploadFile.owner_anon_sub == owner_sub) | (UploadFile.owner_sub == owner_sub),
    )
    if data.file_ids:
        q = q.filter(UploadFile.file_id.in_(data.file_ids))

    rows = q.all()
    for f in rows:
        f.owner_user_id = principal.user_id
        f.owner_anon_sub = None
        f.is_anonymous = False
        db.add(f)
        log_event(
            db,
            "ownership.claim",
            actor_user_id=principal.user_id,
            actor_anon_sub=owner_sub,
            file_id=f.file_id,
        )

    db.commit()
    return {"status": "ok", "claimed": len(rows)}
