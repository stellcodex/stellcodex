from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.ids import format_scx_file_id, normalize_scx_file_id, normalize_scx_id
from app.db.session import get_db
from app.models.file import UploadFile as UploadFileModel
from app.models.orchestrator import OrchestratorSession
from app.security.deps import Principal, get_current_principal
from app.services.audit import log_event
from app.services.orchestrator_sessions import apply_session_state, approval_required, state_label

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


def _normalize_file_uuid(value: str) -> UUID:
    try:
        return normalize_scx_file_id(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file id")


def _public_file_id(value: str) -> str:
    try:
        return normalize_scx_id(value)
    except ValueError:
        return value


def _get_file_by_identifier(db: Session, value: str) -> UploadFileModel | None:
    uid = _normalize_file_uuid(value)
    canonical = format_scx_file_id(uid)
    legacy = str(uid)
    return db.query(UploadFileModel).filter(UploadFileModel.file_id.in_((canonical, legacy))).first()


def _get_session_by_id(db: Session, session_id: str) -> OrchestratorSession:
    try:
        session_uuid = UUID(str(session_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session id")
    session = db.query(OrchestratorSession).filter(OrchestratorSession.id == session_uuid).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


def _assert_file_access(f: UploadFileModel, principal: Principal) -> None:
    if principal.typ == "guest":
        owner_sub = principal.owner_sub or ""
        if f.owner_anon_sub != owner_sub and f.owner_sub != owner_sub:
            raise HTTPException(status_code=403, detail="Forbidden")
        return
    if str(f.owner_user_id or "") != str(principal.user_id or ""):
        raise HTTPException(status_code=403, detail="Forbidden")


def _serialize(session: OrchestratorSession, file_row: UploadFileModel) -> ApprovalOut:
    decision_json = session.decision_json if isinstance(session.decision_json, dict) else {}
    return ApprovalOut(
        session_id=str(session.id),
        file_id=_public_file_id(file_row.file_id),
        state=session.state,
        state_label=state_label(session.state),
        approval_required=approval_required(decision_json),
        decision_json=decision_json,
    )


@router.post("/{session_id}/approve", response_model=ApprovalOut)
def approve_session(
    session_id: str,
    data: ApprovalIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    session = _get_session_by_id(db, session_id)
    file_row = _get_file_by_identifier(db, session.file_id)
    if file_row is None:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(file_row, principal)

    apply_session_state(
        session,
        state="S6 Approved",
        decision_json=session.decision_json if isinstance(session.decision_json, dict) else {},
    )
    db.add(session)
    log_event(
        db,
        "approval.approved",
        actor_user_id=principal.user_id,
        actor_anon_sub=principal.owner_sub,
        file_id=file_row.file_id,
        data={"session_id": str(session.id), "reason": data.reason},
    )
    db.commit()
    db.refresh(session)
    return _serialize(session, file_row)


@router.post("/{session_id}/reject", response_model=ApprovalOut)
def reject_session(
    session_id: str,
    data: ApprovalIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    session = _get_session_by_id(db, session_id)
    file_row = _get_file_by_identifier(db, session.file_id)
    if file_row is None:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(file_row, principal)

    apply_session_state(
        session,
        state="S4 DFMReady",
        decision_json=session.decision_json if isinstance(session.decision_json, dict) else {},
    )
    db.add(session)
    log_event(
        db,
        "approval.rejected",
        actor_user_id=principal.user_id,
        actor_anon_sub=principal.owner_sub,
        file_id=file_row.file_id,
        data={"session_id": str(session.id), "reason": data.reason},
    )
    db.commit()
    db.refresh(session)
    return _serialize(session, file_row)
