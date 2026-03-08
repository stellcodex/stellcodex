from __future__ import annotations

import base64
import io
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.orchestrator import ensure_session_decision
from app.core.ids import format_scx_file_id, normalize_scx_file_id, normalize_scx_id
from app.db.session import get_db
from app.models.file import UploadFile as UploadFileModel
from app.security.deps import Principal, get_current_principal
from app.services.audit import log_event

router = APIRouter(tags=["dfm"])


class DfmRunIn(BaseModel):
    file_id: str


class DfmReportOut(BaseModel):
    file_id: str
    state: str
    state_code: str
    state_label: str
    status_gate: str
    approval_required: bool
    rule_version: str
    mode: str
    confidence: float
    rule_explanations: list[str]
    decision_json: dict
    dfm_findings: dict | None = None
    geometry_report: dict | None = None
    wall_risks: list[dict] = Field(default_factory=list)
    draft_risks: list[dict] = Field(default_factory=list)
    undercut_risks: list[dict] = Field(default_factory=list)
    shrinkage_warnings: list[dict] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    report_hash: str | None = None
    pdf_url: str | None = None


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
    dfm_report = meta.get("dfm_report_json") if isinstance(meta.get("dfm_report_json"), dict) else {}
    dfm_findings = dfm_report if dfm_report else (
        meta.get("dfm_findings") if isinstance(meta.get("dfm_findings"), dict) else None
    )
    geometry_report = meta.get("geometry_report") if isinstance(meta.get("geometry_report"), dict) else None
    state = str(decision_json.get("state") or decision_json.get("state_code") or "S0")
    public_file_id = _public_file_id(f.file_id)
    return DfmReportOut(
        file_id=public_file_id,
        state=state,
        state_code=state,
        state_label=str(decision_json.get("state_label") or "uploaded"),
        status_gate=str(decision_json.get("status_gate") or "PENDING"),
        approval_required=bool(decision_json.get("approval_required")),
        rule_version=str(decision_json.get("rule_version") or "v7.0.0"),
        mode=str(decision_json.get("mode") or "visual_only"),
        confidence=float(decision_json.get("confidence") if isinstance(decision_json.get("confidence"), (int, float)) else 0.05),
        rule_explanations=[str(item) for item in (decision_json.get("rule_explanations") or [])],
        decision_json=decision_json,
        dfm_findings=dfm_findings,
        geometry_report=geometry_report,
        wall_risks=[item for item in (dfm_report.get("wall_risks") or []) if isinstance(item, dict)],
        draft_risks=[item for item in (dfm_report.get("draft_risks") or []) if isinstance(item, dict)],
        undercut_risks=[item for item in (dfm_report.get("undercut_risks") or []) if isinstance(item, dict)],
        shrinkage_warnings=[item for item in (dfm_report.get("shrinkage_warnings") or []) if isinstance(item, dict)],
        recommendations=[str(item) for item in (dfm_report.get("recommendations") or []) if str(item).strip()],
        report_hash=str((dfm_report or {}).get("report_hash") or meta.get("dfm_report_hash") or ""),
        pdf_url=f"/api/v1/dfm/report/pdf?file_id={public_file_id}",
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

    _row, decision_json = ensure_session_decision(db, file_row)
    report_hash = str(((file_row.meta or {}).get("dfm_report_json") or {}).get("report_hash") or "")
    log_event(
        db,
        "dfm.report_generated",
        file_id=file_row.file_id,
        data={"report_hash": report_hash, "state": decision_json.get("state")},
    )
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

    _row, decision_json = ensure_session_decision(db, file_row)

    return _build_report(file_row, decision_json)


@router.get("/dfm/report/pdf")
def get_dfm_report_pdf(
    file_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    normalized_file_id = _normalize_file_id(file_id)
    file_row = _get_file_by_identifier(db, normalized_file_id)
    if not file_row:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(file_row, principal)

    _row, _decision = ensure_session_decision(db, file_row)
    meta = file_row.meta if isinstance(file_row.meta, dict) else {}
    payload = meta.get("dfm_report_pdf_b64")
    if not isinstance(payload, str) or not payload:
        raise HTTPException(status_code=404, detail="DFM PDF report not found")
    try:
        pdf_bytes = base64.b64decode(payload.encode("ascii"), validate=True)
    except Exception:
        raise HTTPException(status_code=500, detail="DFM PDF report payload is invalid")

    filename = f"{_public_file_id(file_row.file_id)}_dfm_report.pdf"
    headers = {"Content-Disposition": f'inline; filename="{filename}"'}
    return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf", headers=headers)
