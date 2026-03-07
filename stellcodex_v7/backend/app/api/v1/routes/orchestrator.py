from __future__ import annotations

from datetime import datetime, timezone
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.ids import format_scx_file_id, normalize_scx_file_id, normalize_scx_id
from app.db.session import get_db
from app.models.file import UploadFile as UploadFileModel
from app.models.orchestrator import OrchestratorSession, RuleConfig
from app.security.deps import Principal, get_current_principal
from app.services.orchestrator_engine import build_decision_json, load_rule_config_map, upsert_orchestrator_session

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


class OrchestratorDecisionOut(BaseModel):
    file_id: str
    state_code: str
    state_label: str
    status_gate: str
    approval_required: bool
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


def _session_payload(row: OrchestratorSession, file_row: UploadFileModel) -> dict:
    return {
        "file_id": _public_file_id(file_row.file_id),
        "state_code": row.state_code,
        "state_label": row.state_label,
        "status_gate": row.status_gate,
        "approval_required": bool(row.approval_required),
        "risk_flags": row.risk_flags if isinstance(row.risk_flags, list) else [],
        "decision_json": row.decision_json if isinstance(row.decision_json, dict) else {},
        "updated_at": row.updated_at,
    }


def _ensure_session_row(db: Session, file_row: UploadFileModel) -> OrchestratorSession:
    row = db.query(OrchestratorSession).filter(OrchestratorSession.file_id == file_row.file_id).first()
    if row is not None:
        return row
    rules = load_rule_config_map(db)
    decision_json = build_decision_json(file_row, rules)
    row = upsert_orchestrator_session(db, file_row, decision_json)
    db.add(file_row)
    db.commit()
    db.refresh(row)
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

    row = _ensure_session_row(db, file_row)
    meta = file_row.meta if isinstance(file_row.meta, dict) else {}
    inputs = meta.get("orchestrator_inputs")
    if not isinstance(inputs, list):
        inputs = []
    inputs.append(
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "input_text": data.input_text,
            "payload": data.payload if isinstance(data.payload, dict) else None,
        }
    )
    file_row.meta = {**meta, "orchestrator_inputs": inputs[-20:]}
    row.notes = f"inputs={len(inputs)}"
    db.add(file_row)
    db.add(row)
    db.commit()
    db.refresh(row)

    return {"status": "accepted", **_session_payload(row, file_row)}


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

    row = _ensure_session_row(db, file_row)
    decision = row.decision_json if isinstance(row.decision_json, dict) else {}

    if row.state_code == "S5" and data.approve:
        next_decision = {
            **decision,
            "state_code": "S6",
            "state_label": "approved_ready",
            "status_gate": "PASS",
            "approval_required": False,
            "decision": "approve_manual",
        }
        row.state_code = "S6"
        row.state_label = "approved_ready"
        row.status_gate = "PASS"
        row.approval_required = False
        row.decision_json = next_decision
        file_row.decision_json = next_decision
        file_row.meta = {**(file_row.meta or {}), "decision_json": next_decision}

    if data.note:
        row.notes = (row.notes or "").strip()
        row.notes = f"{row.notes}; {data.note}".strip("; ")

    db.add(file_row)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"status": "ok", **_session_payload(row, file_row)}


@router.get("/session")
def orchestrator_session_alias(
    file_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    return get_orchestrator_session(file_id=file_id, db=db, principal=principal)


@router.get("/files/{file_id}/decision_json", response_model=OrchestratorDecisionOut)
def orchestrator_decision_json(
    file_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    normalized_file_id = _normalize_file_id(file_id)
    f = _get_file_by_identifier(db, normalized_file_id)
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(f, principal)

    rules = load_rule_config_map(db)
    decision_json = build_decision_json(f, rules)
    f.decision_json = decision_json
    f.meta = {**(f.meta or {}), "decision_json": decision_json}
    db.add(f)
    upsert_orchestrator_session(db, f, decision_json)
    db.commit()

    return OrchestratorDecisionOut(
        file_id=_public_file_id(f.file_id),
        state_code=str(decision_json.get("state_code") or "S0"),
        state_label=str(decision_json.get("state_label") or "uploaded"),
        status_gate=str(decision_json.get("status_gate") or "PENDING"),
        approval_required=bool(decision_json.get("approval_required")),
        risk_flags=[str(item) for item in (decision_json.get("risk_flags") or [])],
        decision_json=decision_json,
    )


@router.get("/sessions/{file_id}")
def get_orchestrator_session(
    file_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    normalized_file_id = _normalize_file_id(file_id)
    f = _get_file_by_identifier(db, normalized_file_id)
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(f, principal)

    row = _ensure_session_row(db, f)
    return _session_payload(row, f)
