from __future__ import annotations

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.orchestrator import ensure_session_decision
from app.core.ids import format_scx_file_id, normalize_scx_file_id, normalize_scx_id
from app.db.session import get_db
from app.models.file import UploadFile as UploadFileModel
from app.models.orchestrator import OrchestratorSession, RuleConfig
from app.security.deps import Principal, get_current_principal

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


class OrchestratorDecisionOut(BaseModel):
    file_id: str
    session_id: str | None = None
    state: str
    state_code: str
    state_label: str
    status_gate: str
    approval_required: bool
    rule_version: str
    mode: str
    confidence: float
    risk_flags: list[str]
    decision_json: dict


class RuleConfigOut(BaseModel):
    key: str
    value_json: dict
    enabled: bool
    description: str | None = None


class OrchestratorStartIn(BaseModel):
    file_id: str


class OrchestratorInputIn(BaseModel):
    file_id: str
    input_text: str | None = None
    payload: dict | None = None


class OrchestratorAdvanceIn(BaseModel):
    file_id: str
    approve: bool = False
    note: str | None = None


def _normalize_file_uuid(value: str) -> UUID:
    try:
        return normalize_scx_file_id(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file id")


def _normalize_file_id(value: str) -> str:
    return format_scx_file_id(_normalize_file_uuid(value))


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


def _session_payload(row: OrchestratorSession, file_row: UploadFileModel, decision_json: dict | None = None) -> dict:
    payload = decision_json if isinstance(decision_json, dict) else (
        row.decision_json if isinstance(row.decision_json, dict) else {}
    )
    state = str(payload.get("state") or row.state or row.state_code or "S0")
    return {
        "file_id": _public_file_id(file_row.file_id),
        "session_id": str(row.id),
        "state": state,
        "state_code": state,
        "state_label": str(payload.get("state_label") or row.state_label or "uploaded"),
        "status_gate": str(payload.get("status_gate") or row.status_gate or "PENDING"),
        "approval_required": bool(payload.get("approval_required") if "approval_required" in payload else row.approval_required),
        "rule_version": str(payload.get("rule_version") or row.rule_version or "v7.0.0"),
        "mode": str(payload.get("mode") or row.mode or "visual_only"),
        "confidence": float(payload.get("confidence") if isinstance(payload.get("confidence"), (int, float)) else row.confidence or 0.05),
        "risk_flags": [str(item) for item in (payload.get("risk_flags") or row.risk_flags or [])],
        "decision_json": payload,
        "updated_at": row.updated_at,
    }


def _ensure_session_row(db: Session, file_row: UploadFileModel) -> tuple[OrchestratorSession, dict]:
    return ensure_session_decision(db, file_row)


def _get_session_by_id(db: Session, session_id: str) -> OrchestratorSession:
    try:
        sid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session id")
    row = db.query(OrchestratorSession).filter(OrchestratorSession.id == sid).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return row


@router.get("/rules", response_model=List[RuleConfigOut])
def list_rule_configs(
    db: Session = Depends(get_db),
    _principal: Principal = Depends(get_current_principal),
):
    rows = db.query(RuleConfig).order_by(RuleConfig.key.asc()).all()
    return [
        RuleConfigOut(
            key=row.key,
            value_json=row.value_json if isinstance(row.value_json, dict) else {},
            enabled=bool(row.enabled),
            description=row.description,
        )
        for row in rows
    ]


@router.post("/start", response_model=OrchestratorDecisionOut)
def orchestrator_start(
    data: OrchestratorStartIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    return orchestrator_decision_json(file_id=data.file_id, db=db, principal=principal)


@router.post("/input")
def orchestrator_input(
    data: OrchestratorInputIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    normalized_file_id = _normalize_file_id(data.file_id)
    file_row = _get_file_by_identifier(db, normalized_file_id)
    if not file_row:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(file_row, principal)

    row, decision_json = ensure_session_decision(
        db,
        file_row,
        input_text=data.input_text,
        payload=data.payload if isinstance(data.payload, dict) else None,
    )
    return {"status": "accepted", **_session_payload(row, file_row, decision_json)}


@router.post("/advance")
def orchestrator_advance(
    data: OrchestratorAdvanceIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    normalized_file_id = _normalize_file_id(data.file_id)
    file_row = _get_file_by_identifier(db, normalized_file_id)
    if not file_row:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(file_row, principal)

    row, decision = _ensure_session_row(db, file_row)
    next_decision = dict(decision)
    if data.approve:
        state = str(next_decision.get("state") or "S0")
        if state not in {"S5", "S6"}:
            raise HTTPException(status_code=409, detail="Approval allowed only from S5 or S6")
        meta = file_row.meta if isinstance(file_row.meta, dict) else {}
        meta["approval_override"] = "approved"
        if data.note:
            meta["approval_note"] = data.note
        file_row.meta = meta
        row, next_decision = ensure_session_decision(db, file_row)

    if data.note:
        row.notes = (row.notes or "").strip()
        row.notes = f"{row.notes}; {data.note}".strip("; ")
        db.add(row)
        db.commit()
        db.refresh(row)
    return {"status": "ok", **_session_payload(row, file_row, next_decision)}


@router.get("/session")
def orchestrator_session_alias(
    file_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    return get_orchestrator_session(file_id=file_id, db=db, principal=principal)


@router.get("/decision", response_model=OrchestratorDecisionOut)
def orchestrator_decision_by_session(
    session_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    row = _get_session_by_id(db, session_id)
    file_row = _get_file_by_identifier(db, row.file_id)
    if file_row is None:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(file_row, principal)
    row, decision_json = _ensure_session_row(db, file_row)
    return OrchestratorDecisionOut(**_session_payload(row, file_row, decision_json))


@router.get("/files/{file_id}/decision_json", response_model=OrchestratorDecisionOut)
def orchestrator_decision_json(
    file_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    normalized_file_id = _normalize_file_id(file_id)
    file_row = _get_file_by_identifier(db, normalized_file_id)
    if not file_row:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(file_row, principal)
    row, decision_json = _ensure_session_row(db, file_row)
    return OrchestratorDecisionOut(**_session_payload(row, file_row, decision_json))


@router.get("/sessions/{file_id}")
def get_orchestrator_session(
    file_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    normalized_file_id = _normalize_file_id(file_id)
    file_row = _get_file_by_identifier(db, normalized_file_id)
    if not file_row:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(file_row, principal)
    row, decision_json = _ensure_session_row(db, file_row)
    return _session_payload(row, file_row, decision_json)
