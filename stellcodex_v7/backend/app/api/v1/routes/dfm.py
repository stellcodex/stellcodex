from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.ids import format_scx_file_id, normalize_scx_file_id, normalize_scx_id
from app.db.session import get_db
from app.models.file import UploadFile as UploadFileModel
from app.security.deps import Principal, get_current_principal
from app.services.orchestrator_engine import build_decision_json, load_rule_config_map, upsert_orchestrator_session

router = APIRouter(tags=["dfm"])


class DfmRunIn(BaseModel):
    file_id: str


class DfmReportOut(BaseModel):
    file_id: str
    state_code: str
    status_gate: str
    approval_required: bool
    decision_json: dict
    dfm_findings: dict | None = None
    geometry_report: dict | None = None


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


def _build_report(f: UploadFileModel, decision_json: dict) -> DfmReportOut:
    meta = f.meta if isinstance(f.meta, dict) else {}
    dfm_findings = meta.get("dfm_findings") if isinstance(meta.get("dfm_findings"), dict) else None
    geometry_report = meta.get("geometry_report") if isinstance(meta.get("geometry_report"), dict) else None
    return DfmReportOut(
        file_id=_public_file_id(f.file_id),
        state_code=str(decision_json.get("state_code") or "S0"),
        status_gate=str(decision_json.get("status_gate") or "PENDING"),
        approval_required=bool(decision_json.get("approval_required")),
        decision_json=decision_json,
        dfm_findings=dfm_findings,
        geometry_report=geometry_report,
    )


@router.post("/dfm/run", response_model=DfmReportOut)
def run_dfm(
    data: DfmRunIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    normalized_file_id = _normalize_file_id(data.file_id)
    file_row = _get_file_by_identifier(db, normalized_file_id)
    if not file_row:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(file_row, principal)

    rules = load_rule_config_map(db)
    decision_json = build_decision_json(file_row, rules)
    file_row.decision_json = decision_json
    file_row.meta = {**(file_row.meta or {}), "decision_json": decision_json}
    db.add(file_row)
    upsert_orchestrator_session(db, file_row, decision_json)
    db.commit()

    return _build_report(file_row, decision_json)


@router.get("/dfm/report", response_model=DfmReportOut)
def get_dfm_report(
    file_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    normalized_file_id = _normalize_file_id(file_id)
    file_row = _get_file_by_identifier(db, normalized_file_id)
    if not file_row:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(file_row, principal)

    decision_json = file_row.decision_json if isinstance(file_row.decision_json, dict) else {}
    if not decision_json:
        rules = load_rule_config_map(db)
        decision_json = build_decision_json(file_row, rules)
        file_row.decision_json = decision_json
        file_row.meta = {**(file_row.meta or {}), "decision_json": decision_json}
        db.add(file_row)
        upsert_orchestrator_session(db, file_row, decision_json)
        db.commit()

    return _build_report(file_row, decision_json)
