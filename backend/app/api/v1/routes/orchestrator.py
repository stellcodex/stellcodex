from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.v1.routes._file_access import (
    assert_file_access,
    file_for_session,
    get_file_by_identifier,
    public_file_id,  # noqa: F401 – re-exported for potential future route use
)
from app.db.session import get_db
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

    Backend validates ownership/file access here; Orchestra remains the sole
    authority for workflow decisions and state transitions. This function does
    NOT make workflow decisions — it only enforces the auth/ownership boundary
    before forwarding the request.
    """
    if session_id:
        file_for_session(db, session_id, principal)
        query = {"session_id": session_id}
    else:
        file_row = get_file_by_identifier(db, str(file_id))
        if file_row is None:
            raise HTTPException(status_code=404, detail="File not found")
        assert_file_access(file_row, principal)
        query = {"file_id": file_row.file_id}

    return proxy_orchestra(path=path, method=method, query=query if method == "GET" else None, payload=payload)


@router.post("/start", response_model=OrchestratorDecisionOut)
def start_orchestrator(
    file_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    file_row = get_file_by_identifier(db, file_id)
    if file_row is None:
        raise HTTPException(status_code=404, detail="File not found")
    assert_file_access(file_row, principal)

    payload = proxy_orchestra(path="/sessions/start", method="POST", payload={"file_id": file_row.file_id})

    # Observability record: backend logs the session and state that Orchestra returned.
    # The start decision and state assignment are Orchestra-owned; backend records what
    # Orchestra reported so the event trail is visible in admin audit surfaces.
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
    file_for_session(db, session_id, principal)
    return proxy_orchestra(path="/sessions/required-inputs", query={"session_id": session_id})


@router.post("/input", response_model=OrchestratorInputOut)
def submit_orchestrator_input(
    data: OrchestratorInputIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    file_for_session(db, data.session_id, principal)
    return proxy_orchestra(path="/sessions/input", method="POST", payload=data.model_dump())


@router.post("/advance", response_model=OrchestratorAdvanceOut)
def advance_orchestrator(
    data: OrchestratorAdvanceIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    file_row = file_for_session(db, data.session_id, principal)
    payload = proxy_orchestra(path="/sessions/advance", method="POST", payload=data.model_dump())

    # Observability record: backend logs the state transition that Orchestra returned.
    # The advance decision and resulting state are Orchestra-owned; backend records
    # what Orchestra reported so admin audit surfaces remain complete.
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
