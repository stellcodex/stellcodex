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
from app.services.orchestra_client import proxy_orchestra

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


class OrchestratorDecisionOut(BaseModel):
    session_id: str
    file_id: str
    state: str
    state_label: str
    approval_required: bool
    risk_flags: list[str] = Field(default_factory=list)
    decision_json: dict[str, Any]


class RequiredInputOut(BaseModel):
    key: str
    label: str
    input_type: str
    required: bool = True


class BlockedReasonOut(BaseModel):
    code: str
    message: str


class RequiredInputsOut(BaseModel):
    session_id: str
    file_id: str
    required_inputs: list[RequiredInputOut] = Field(default_factory=list)
    submitted_inputs: dict[str, Any] = Field(default_factory=dict)
    blocked_reasons: list[BlockedReasonOut] = Field(default_factory=list)


class OrchestratorInputIn(BaseModel):
    session_id: str
    key: str
    value: Any


class OrchestratorInputOut(BaseModel):
    session_id: str
    file_id: str
    state: str
    state_label: str
    accepted: bool = True
    submitted_inputs: dict[str, Any] = Field(default_factory=dict)
    required_inputs: list[RequiredInputOut] = Field(default_factory=list)


class OrchestratorAdvanceIn(BaseModel):
    session_id: str


class OrchestratorAdvanceOut(BaseModel):
    session_id: str
    file_id: str
    state: str
    state_label: str
    advanced: bool
    decision_json: dict[str, Any]
    required_inputs: list[RequiredInputOut] = Field(default_factory=list)
    blocked_reasons: list[BlockedReasonOut] = Field(default_factory=list)


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


def _assert_file_access(file_row: UploadFileModel, principal: Principal) -> None:
    if str(file_row.owner_user_id or "") != str(principal.user_id or ""):
        raise HTTPException(status_code=403, detail="Forbidden")


def _get_session_by_id(db: Session, session_id: str) -> OrchestratorSession:
    try:
        session_uuid = UUID(str(session_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session id")
    session = db.query(OrchestratorSession).filter(OrchestratorSession.id == session_uuid).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


def _file_for_session(db: Session, session_id: str, principal: Principal) -> UploadFileModel:
    session = _get_session_by_id(db, session_id)
    file_row = _get_file_by_identifier(db, session.file_id)
    if file_row is None:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(file_row, principal)
    return file_row

def _proxy_orchestra_for_owned_file(
    *,
    db: Session,
    principal: Principal,
    path: str,
    method: str = "GET",
    file_id: str | None = None,
    session_id: str | None = None,
    payload: dict[str, Any] | None = None,
):
    """Backend gateway guard for orchestrator proxy calls.

    Backend validates ownership/file access, while Orchestra remains the
    authority for workflow decisions and state transitions.
    """
    if session_id:
        _file_for_session(db, session_id, principal)
        query = {"session_id": session_id}
    else:
        file_row = _get_file_by_identifier(db, str(file_id))
        if file_row is None:
            raise HTTPException(status_code=404, detail="File not found")
        _assert_file_access(file_row, principal)
        query = {"file_id": file_row.file_id}

    return proxy_orchestra(path=path, method=method, query=query if method == "GET" else None, payload=payload)



@router.post("/start", response_model=OrchestratorDecisionOut)
def start_orchestrator(
    file_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    file_row = _get_file_by_identifier(db, file_id)
    if file_row is None:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(file_row, principal)

    payload = proxy_orchestra(path="/sessions/start", method="POST", payload={"file_id": file_row.file_id})
    log_event(
        db,
        "orchestrator.started",
        actor_user_id=principal.user_id,
        actor_anon_sub=principal.owner_sub,
        file_id=file_row.file_id,
        data={"session_id": payload.get("session_id"), "state": payload.get("state")},
    )
    db.commit()
    return payload


@router.get("/decision", response_model=OrchestratorDecisionOut)
def get_orchestrator_decision(
    file_id: str | None = None,
    session_id: str | None = None,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    if not file_id and not session_id:
        raise HTTPException(status_code=400, detail="file_id or session_id is required")

    return _proxy_orchestra_for_owned_file(
        db=db,
        principal=principal,
        path="/sessions/decision",
        file_id=file_id,
        session_id=session_id,
    )


@router.get("/required-inputs", response_model=RequiredInputsOut)
def get_required_inputs(
    session_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    _file_for_session(db, session_id, principal)
    return proxy_orchestra(path="/sessions/required-inputs", query={"session_id": session_id})


@router.post("/input", response_model=OrchestratorInputOut)
def submit_orchestrator_input(
    data: OrchestratorInputIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    _file_for_session(db, data.session_id, principal)
    return proxy_orchestra(path="/sessions/input", method="POST", payload=data.model_dump())


@router.post("/advance", response_model=OrchestratorAdvanceOut)
def advance_orchestrator(
    data: OrchestratorAdvanceIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    file_row = _file_for_session(db, data.session_id, principal)
    payload = proxy_orchestra(path="/sessions/advance", method="POST", payload=data.model_dump())
    log_event(
        db,
        "orchestrator.advanced",
        actor_user_id=principal.user_id,
        actor_anon_sub=principal.owner_sub,
        file_id=file_row.file_id,
        data={"session_id": data.session_id, "state": payload.get("state")},
    )
    db.commit()
    return payload
