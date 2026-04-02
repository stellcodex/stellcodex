from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.v1.routes._file_access import file_for_session
from app.db.session import get_db
from app.security.deps import Principal, get_current_principal
from app.services.audit import log_event
from app.services.orchestra_client import proxy_orchestra

router = APIRouter(prefix="/approvals", tags=["approvals"])


class ApprovalIn(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class ApprovalOut(BaseModel):
    session_id: str
    file_id: str
    state: str
    state_label: str
    approval_required: bool
    decision_json: dict[str, Any]


@router.post("/{session_id}/approve", response_model=ApprovalOut)
def approve_session(
    session_id: str,
    data: ApprovalIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    """Owner-initiated approval for a pending orchestrator session.

    Access model: the authenticated principal must own the file associated with
    the session. This surface is distinct from the admin approval surface
    (/admin/approvals/{id}:approve), which requires an admin role instead of
    file ownership. Both surfaces proxy to the same Orchestra endpoint.
    """
    file_row = file_for_session(db, session_id, principal)
    payload = proxy_orchestra(
        path="/sessions/approve",
        method="POST",
        payload={"session_id": session_id, "reason": data.reason},
    )
    log_event(
        db,
        "approval.approved",
        actor_user_id=principal.user_id,
        actor_anon_sub=principal.owner_sub,
        file_id=file_row.file_id,
        data={"session_id": session_id, "reason": data.reason},
    )
    db.commit()
    return payload


@router.post("/{session_id}/reject", response_model=ApprovalOut)
def reject_session(
    session_id: str,
    data: ApprovalIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    """Owner-initiated rejection for a pending orchestrator session.

    Access model: the authenticated principal must own the file associated with
    the session. This surface is distinct from the admin rejection surface
    (/admin/approvals/{id}:reject), which requires an admin role instead of
    file ownership. Both surfaces proxy to the same Orchestra endpoint.
    """
    file_row = file_for_session(db, session_id, principal)
    payload = proxy_orchestra(
        path="/sessions/reject",
        method="POST",
        payload={"session_id": session_id, "reason": data.reason},
    )
    log_event(
        db,
        "approval.rejected",
        actor_user_id=principal.user_id,
        actor_anon_sub=principal.owner_sub,
        file_id=file_row.file_id,
        data={"session_id": session_id, "reason": data.reason},
    )
    db.commit()
    return payload
