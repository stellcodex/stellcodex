from __future__ import annotations

import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.event_bus import default_event_bus
from app.core.event_types import EventType
from app.core.memory_foundation import write_memory_payload
from app.core.read_model import upsert_projection
from app.db.session import get_db
from app.models.file import UploadFile as UploadFileModel
from app.models.orchestrator import OrchestratorSession
from app.security.deps import Principal, get_current_principal
from app.services.audit import log_event
from app.services.orchestrator_engine import load_rule_config_map, normalize_decision_json, upsert_orchestrator_session

router = APIRouter(prefix="/approvals", tags=["approvals"])


class ApprovalActionIn(BaseModel):
    note: str | None = None


class ApprovalActionOut(BaseModel):
    file_id: str
    session_id: str
    state: str
    status_gate: str
    approval_required: bool


def _require_user(principal: Principal) -> None:
    if principal.typ != "user":
        raise HTTPException(status_code=401, detail="User token required")


def _allowed_role(role: str | None) -> bool:
    return str(role or "").strip().lower() in {"admin", "support"}


def _load_session(db: Session, session_id: str) -> OrchestratorSession:
    try:
        sid = UUID(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session id")
    row = db.query(OrchestratorSession).filter(OrchestratorSession.id == sid).first()
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return row


def _load_file_for_session(db: Session, row: OrchestratorSession) -> UploadFileModel:
    file_row = db.query(UploadFileModel).filter(UploadFileModel.file_id == row.file_id).first()
    if file_row is None:
        raise HTTPException(status_code=404, detail="File not found")
    return file_row


def _assert_approval_access(file_row: UploadFileModel, principal: Principal) -> None:
    _require_user(principal)
    if _allowed_role(principal.role):
        return
    if str(file_row.owner_user_id or "") != str(principal.user_id or ""):
        raise HTTPException(status_code=403, detail="Forbidden")


def _ensure_canonical_decision(db: Session, file_row: UploadFileModel, row: OrchestratorSession) -> dict:
    rules = load_rule_config_map(db)
    decision = normalize_decision_json(file_row, rules, row.decision_json or file_row.decision_json)
    state = str(decision.get("state") or "S0")
    approval_required = bool(decision.get("approval_required"))
    if approval_required and state in {"S6", "S7"}:
        decision["state"] = "S5"
        decision["state_code"] = "S5"
        decision["state_label"] = "awaiting_approval"
        decision["status_gate"] = "NEEDS_APPROVAL"
        decision["approval_required"] = True
    return decision


def _append_reason(decision: dict, text: str) -> None:
    reasons = decision.get("rule_explanations")
    if not isinstance(reasons, list):
        reasons = []
    reasons.append(text)
    decision["rule_explanations"] = [str(item) for item in reasons if str(item).strip()]


def _append_conflict(decision: dict, code: str) -> None:
    flags = decision.get("conflict_flags")
    if not isinstance(flags, list):
        flags = []
    flags.append(code)
    decision["conflict_flags"] = sorted({str(item) for item in flags if str(item).strip()})


def _approval_response(file_row: UploadFileModel, row: OrchestratorSession, decision: dict) -> ApprovalActionOut:
    return ApprovalActionOut(
        file_id=file_row.file_id,
        session_id=str(row.id),
        state=str(decision.get("state") or row.state or "S0"),
        status_gate=str(decision.get("status_gate") or row.status_gate or "PENDING"),
        approval_required=bool(decision.get("approval_required")),
    )


def _approval_transition_path(state: str) -> list[str]:
    if state == "S4":
        return ["S5", "S6", "S7"]
    if state == "S5":
        return ["S6", "S7"]
    if state == "S6":
        return ["S7"]
    return []


@router.post("/{session_id}/approve", response_model=ApprovalActionOut)
def approve_session(
    session_id: str,
    payload: ApprovalActionIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    row = _load_session(db, session_id)
    file_row = _load_file_for_session(db, row)
    _assert_approval_access(file_row, principal)
    decision = _ensure_canonical_decision(db, file_row, row)

    state = str(decision.get("state") or "S0")
    if state not in {"S4", "S5", "S6", "S7"}:
        raise HTTPException(status_code=409, detail="Session state is not approvable")
    if bool(decision.get("approval_required")) and state not in {"S4", "S5"}:
        raise HTTPException(status_code=409, detail="Approval-required session must be in S4 or S5")

    transition_path = _approval_transition_path(state)

    decision["state"] = "S7"
    decision["state_code"] = "S7"
    decision["state_label"] = "share_ready"
    decision["status_gate"] = "PASS"
    decision["approval_required"] = False
    decision["decision"] = "approve_manual"
    decision["state_transition_path"] = [state] + transition_path if transition_path else [state]
    _append_reason(
        decision,
        f"manual approval accepted; transition path={'->'.join([state] + transition_path)}.",
    )
    if payload.note:
        _append_reason(decision, f"approval note: {payload.note}")
    decision["conflict_flags"] = [f for f in decision.get("conflict_flags", []) if f != "approval_rejected"]

    meta = file_row.meta if isinstance(file_row.meta, dict) else {}
    meta["approval_override"] = "approved"
    meta["decision_json"] = decision
    file_row.meta = meta
    file_row.decision_json = decision
    row = upsert_orchestrator_session(db, file_row, decision)
    upsert_projection(db, file_row)
    db.add(file_row)
    db.add(row)
    log_event(
        db,
        "approval.approved",
        actor_user_id=principal.user_id,
        file_id=file_row.file_id,
        data={
            "session_id": str(row.id),
            "from_state": state,
            "to_state": "S7",
            "transition_path": transition_path,
            "note": payload.note,
        },
    )
    try:
        default_event_bus().publish_event(
            event_type=EventType.APPROVAL_APPROVED.value,
            source="api.approvals",
            subject=file_row.file_id,
            tenant_id=str(file_row.tenant_id),
            project_id=str((file_row.meta or {}).get("project_id") or "default"),
            data={
                "file_id": file_row.file_id,
                "session_id": str(row.id),
                "from_state": state,
                "to_state": "S7",
                "transition_path": transition_path,
                "note": payload.note,
            },
        )
        default_event_bus().publish_event(
            event_type="approval.changed",
            source="api.approvals",
            subject=file_row.file_id,
            tenant_id=str(file_row.tenant_id),
            project_id=str((file_row.meta or {}).get("project_id") or "default"),
            data={
                "action": "approved",
                "file_id": file_row.file_id,
                "session_id": str(row.id),
                "from_state": state,
                "to_state": "S7",
                "transition_path": transition_path,
                "note": payload.note,
                "actor_user_id": str(principal.user_id or ""),
            },
        )
    except Exception:
        pass
    try:
        memory_path = write_memory_payload(
            record_type="approval_log",
            title="Approval accepted",
            source_uri=f"scx://files/{file_row.file_id}/approval/{row.id}",
            tenant_id=str(file_row.tenant_id),
            project_id=str((file_row.meta or {}).get("project_id") or "default"),
            tags=["phase2", "approval", "approved"],
            text=json.dumps(
                {
                    "file_id": file_row.file_id,
                    "session_id": str(row.id),
                    "from_state": state,
                    "to_state": "S7",
                    "note": payload.note,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            metadata={
                "file_id": file_row.file_id,
                "session_id": str(row.id),
                "action": "approved",
                "actor_user_id": str(principal.user_id or ""),
            },
        )
        file_row.meta = {**(file_row.meta or {}), "approval_memory_record": str(memory_path)}
        db.add(file_row)
    except Exception:
        pass
    db.commit()
    db.refresh(row)
    return _approval_response(file_row, row, decision)


@router.post("/{session_id}/reject", response_model=ApprovalActionOut)
def reject_session(
    session_id: str,
    payload: ApprovalActionIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    row = _load_session(db, session_id)
    file_row = _load_file_for_session(db, row)
    _assert_approval_access(file_row, principal)
    decision = _ensure_canonical_decision(db, file_row, row)

    state = str(decision.get("state") or "S0")
    if state not in {"S4", "S5", "S6", "S7"}:
        raise HTTPException(status_code=409, detail="Session state is not rejectable")

    decision["state"] = "S4"
    decision["state_code"] = "S4"
    decision["state_label"] = "dfm_ready"
    decision["status_gate"] = "NEEDS_APPROVAL"
    decision["approval_required"] = True
    decision["decision"] = "reject_manual"
    _append_conflict(decision, "approval_rejected")
    _append_reason(decision, "manual approval rejected; session returned to S4 by policy.")
    if payload.note:
        _append_reason(decision, f"rejection note: {payload.note}")

    meta = file_row.meta if isinstance(file_row.meta, dict) else {}
    meta["approval_override"] = "rejected"
    meta["decision_json"] = decision
    file_row.meta = meta
    file_row.decision_json = decision
    row = upsert_orchestrator_session(db, file_row, decision)
    upsert_projection(db, file_row)
    db.add(file_row)
    db.add(row)
    log_event(
        db,
        "approval.rejected",
        actor_user_id=principal.user_id,
        file_id=file_row.file_id,
        data={
            "session_id": str(row.id),
            "from_state": state,
            "to_state": "S4",
            "note": payload.note,
        },
    )
    try:
        default_event_bus().publish_event(
            event_type=EventType.APPROVAL_REJECTED.value,
            source="api.approvals",
            subject=file_row.file_id,
            tenant_id=str(file_row.tenant_id),
            project_id=str((file_row.meta or {}).get("project_id") or "default"),
            data={
                "file_id": file_row.file_id,
                "session_id": str(row.id),
                "from_state": state,
                "to_state": "S4",
                "note": payload.note,
            },
        )
        default_event_bus().publish_event(
            event_type="approval.changed",
            source="api.approvals",
            subject=file_row.file_id,
            tenant_id=str(file_row.tenant_id),
            project_id=str((file_row.meta or {}).get("project_id") or "default"),
            data={
                "action": "rejected",
                "file_id": file_row.file_id,
                "session_id": str(row.id),
                "from_state": state,
                "to_state": "S4",
                "note": payload.note,
                "actor_user_id": str(principal.user_id or ""),
            },
        )
    except Exception:
        pass
    try:
        memory_path = write_memory_payload(
            record_type="approval_log",
            title="Approval rejected",
            source_uri=f"scx://files/{file_row.file_id}/approval/{row.id}",
            tenant_id=str(file_row.tenant_id),
            project_id=str((file_row.meta or {}).get("project_id") or "default"),
            tags=["phase2", "approval", "rejected"],
            text=json.dumps(
                {
                    "file_id": file_row.file_id,
                    "session_id": str(row.id),
                    "from_state": state,
                    "to_state": "S4",
                    "note": payload.note,
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            metadata={
                "file_id": file_row.file_id,
                "session_id": str(row.id),
                "action": "rejected",
                "actor_user_id": str(principal.user_id or ""),
            },
        )
        file_row.meta = {**(file_row.meta or {}), "approval_memory_record": str(memory_path)}
        db.add(file_row)
    except Exception:
        pass
    db.commit()
    db.refresh(row)
    return _approval_response(file_row, row, decision)
