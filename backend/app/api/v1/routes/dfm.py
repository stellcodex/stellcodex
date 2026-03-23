from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.ids import format_scx_file_id, normalize_scx_file_id, normalize_scx_id
from app.db.session import get_db
from app.models.file import UploadFile as UploadFileModel
from app.security.deps import Principal, get_current_principal
from app.services.stell_ai_client import decide_with_stell_ai

router = APIRouter(prefix="/dfm", tags=["dfm"])


class DfmReportOut(BaseModel):
    file_id: str
    status_gate: str
    risk_flags: list[str] = Field(default_factory=list)
    findings: list[dict[str, Any]] = Field(default_factory=list)
    geometry_report: dict[str, Any] = Field(default_factory=dict)
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


def _assert_file_access(f: UploadFileModel, principal: Principal) -> None:
    if str(f.owner_user_id or "") != str(principal.user_id or ""):
        raise HTTPException(status_code=403, detail="Forbidden")


@router.get("/report", response_model=DfmReportOut)
def get_dfm_report(
    file_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    file_row = _get_file_by_identifier(db, file_id)
    if file_row is None:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(file_row, principal)

    meta = file_row.meta if isinstance(file_row.meta, dict) else {}
    dfm_findings = meta.get("dfm_findings") if isinstance(meta.get("dfm_findings"), dict) else {}
    geometry_report = meta.get("geometry_report") if isinstance(meta.get("geometry_report"), dict) else {}
    decision_json = (
        meta.get("decision_json")
        if isinstance(meta.get("decision_json"), dict)
        else file_row.decision_json if isinstance(file_row.decision_json, dict) else None
    )
    if not isinstance(decision_json, dict):
        decision_json = decide_with_stell_ai(
            file_id=file_row.file_id,
            project_id=str(meta.get("project_id") or "default"),
            mode=str(meta.get("mode") or "visual_only"),
            rule_version=str(meta.get("rule_version") or ""),
            geometry_meta=meta.get("geometry_meta_json") if isinstance(meta.get("geometry_meta_json"), dict) else None,
            dfm_findings=dfm_findings,
        )

    findings = dfm_findings.get("findings")
    risk_flags = dfm_findings.get("risk_flags")
    return DfmReportOut(
        file_id=_public_file_id(file_row.file_id),
        status_gate=str(dfm_findings.get("status_gate") or "UNKNOWN"),
        risk_flags=[str(item) for item in risk_flags] if isinstance(risk_flags, list) else [],
        findings=[item for item in findings if isinstance(item, dict)] if isinstance(findings, list) else [],
        geometry_report=geometry_report,
        decision_json=decision_json,
    )
