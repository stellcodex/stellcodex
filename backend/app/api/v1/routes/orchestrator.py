from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.format_registry import get_rule_for_filename
from app.core.ids import format_scx_file_id, normalize_scx_file_id, normalize_scx_id
from app.db.session import get_db
from app.models.file import UploadFile as UploadFileModel
from app.models.orchestrator import OrchestratorSession
from app.security.deps import Principal, get_current_principal
from app.services.audit import log_event
from app.services.orchestrator_sessions import (
    approval_required,
    build_decision_json,
    derive_session_state,
    state_label,
    upsert_orchestrator_session,
)

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


class RequiredInputsOut(BaseModel):
    session_id: str
    file_id: str
    required_inputs: list[RequiredInputOut] = Field(default_factory=list)


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


def _assert_file_access(f: UploadFileModel, principal: Principal) -> None:
    if principal.typ == "guest":
        owner_sub = principal.owner_sub or ""
        if f.owner_anon_sub != owner_sub and f.owner_sub != owner_sub:
            raise HTTPException(status_code=403, detail="Forbidden")
        return
    if str(f.owner_user_id or "") != str(principal.user_id or ""):
        raise HTTPException(status_code=403, detail="Forbidden")


def _kind_mode(file_row: UploadFileModel) -> tuple[str, str]:
    meta = file_row.meta if isinstance(file_row.meta, dict) else {}
    rule = get_rule_for_filename(file_row.original_filename or "")
    kind = str(meta.get("kind") or (rule.kind if rule else "3d"))
    mode = str(meta.get("mode") or (rule.mode if rule else "brep"))
    return kind, mode


def _decision_json_for_file(file_row: UploadFileModel) -> dict[str, Any]:
    meta = file_row.meta if isinstance(file_row.meta, dict) else {}
    payload = meta.get("decision_json")
    if isinstance(payload, dict):
        return payload
    _kind, mode = _kind_mode(file_row)
    return build_decision_json(
        mode=mode,
        rule_version=str(meta.get("rule_version") or "v0.0"),
        geometry_meta=meta.get("geometry_meta_json") if isinstance(meta.get("geometry_meta_json"), dict) else None,
        dfm_findings=meta.get("dfm_findings") if isinstance(meta.get("dfm_findings"), dict) else None,
    )


def _dfm_findings_for_file(file_row: UploadFileModel) -> dict[str, Any] | None:
    meta = file_row.meta if isinstance(file_row.meta, dict) else {}
    payload = meta.get("dfm_findings")
    return payload if isinstance(payload, dict) else None


def _required_inputs_for_session(session: OrchestratorSession, file_row: UploadFileModel) -> list[RequiredInputOut]:
    decision_json = session.decision_json if isinstance(session.decision_json, dict) else {}
    flags = decision_json.get("conflict_flags")
    items: list[RequiredInputOut] = []
    if isinstance(flags, list) and "unknown_critical_geometry" in flags:
        items.append(
            RequiredInputOut(
                key="geometry_confirmation",
                label="Geometry Confirmation",
                input_type="boolean",
            )
        )
    if approval_required(decision_json, _dfm_findings_for_file(file_row)):
        items.append(
            RequiredInputOut(
                key="approval_reason",
                label="Approval Reason",
                input_type="text",
            )
        )
    return items


def _serialize_session(file_row: UploadFileModel, session: OrchestratorSession) -> OrchestratorDecisionOut:
    decision_json = session.decision_json if isinstance(session.decision_json, dict) else _decision_json_for_file(file_row)
    flags = decision_json.get("conflict_flags")
    return OrchestratorDecisionOut(
        session_id=str(session.id),
        file_id=_public_file_id(file_row.file_id),
        state=session.state,
        state_label=state_label(session.state),
        approval_required=approval_required(decision_json, _dfm_findings_for_file(file_row)),
        risk_flags=[str(item) for item in flags] if isinstance(flags, list) else [],
        decision_json=decision_json,
    )


def _ensure_session(file_row: UploadFileModel, db: Session) -> OrchestratorSession:
    session = db.query(OrchestratorSession).filter(OrchestratorSession.file_id == file_row.file_id).first()
    decision_json = _decision_json_for_file(file_row)
    kind, mode = _kind_mode(file_row)
    dfm_findings = _dfm_findings_for_file(file_row)
    next_state = derive_session_state(
        file_status=file_row.status,
        kind=kind,
        decision_json=decision_json,
        dfm_findings=dfm_findings,
        current_state=session.state if session else None,
    )
    session = upsert_orchestrator_session(
        db,
        file_id=file_row.file_id,
        state=next_state,
        decision_json=decision_json,
        rule_version=str(decision_json.get("rule_version") or "v0.0"),
        mode=mode,
    )
    if session is None:
        raise HTTPException(status_code=503, detail="Orchestrator session store unavailable")
    return session


def _get_session_by_id(db: Session, session_id: str) -> OrchestratorSession:
    try:
        session_uuid = UUID(str(session_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session id")
    session = db.query(OrchestratorSession).filter(OrchestratorSession.id == session_uuid).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


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

    session = _ensure_session(file_row, db)
    log_event(
        db,
        "orchestrator.started",
        actor_user_id=principal.user_id,
        actor_anon_sub=principal.owner_sub,
        file_id=file_row.file_id,
        data={"session_id": str(session.id), "state": session.state},
    )
    db.commit()
    db.refresh(session)
    return _serialize_session(file_row, session)


@router.get("/decision", response_model=OrchestratorDecisionOut)
def get_orchestrator_decision(
    file_id: str | None = None,
    session_id: str | None = None,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    if not file_id and not session_id:
        raise HTTPException(status_code=400, detail="file_id or session_id is required")

    if session_id:
        session = _get_session_by_id(db, session_id)
        file_row = _get_file_by_identifier(db, session.file_id)
        if file_row is None:
            raise HTTPException(status_code=404, detail="File not found")
        _assert_file_access(file_row, principal)
        return _serialize_session(file_row, session)

    file_row = _get_file_by_identifier(db, str(file_id))
    if file_row is None:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(file_row, principal)
    session = _ensure_session(file_row, db)
    db.commit()
    db.refresh(session)
    return _serialize_session(file_row, session)


@router.get("/required-inputs", response_model=RequiredInputsOut)
def get_required_inputs(
    session_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    session = _get_session_by_id(db, session_id)
    file_row = _get_file_by_identifier(db, session.file_id)
    if file_row is None:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(file_row, principal)
    return RequiredInputsOut(
        session_id=str(session.id),
        file_id=_public_file_id(file_row.file_id),
        required_inputs=_required_inputs_for_session(session, file_row),
    )
