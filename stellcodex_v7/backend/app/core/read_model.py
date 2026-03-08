from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.file import UploadFile
from app.models.phase2 import FileReadProjection


def _as_list_of_str(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [str(item) for item in raw if str(item).strip()]


def _decision_payload(file_row: UploadFile) -> dict[str, Any]:
    decision = file_row.decision_json if isinstance(file_row.decision_json, dict) else {}
    meta = file_row.meta if isinstance(file_row.meta, dict) else {}
    if not decision and isinstance(meta.get("decision_json"), dict):
        decision = meta.get("decision_json")
    return decision if isinstance(decision, dict) else {}


def _latest_state(file_row: UploadFile, decision: dict[str, Any]) -> str:
    state = str(decision.get("state") or decision.get("state_code") or "").strip()
    if state:
        return state
    status = str(file_row.status or "queued").strip().lower()
    if status in {"ready", "succeeded"}:
        return "S7"
    if status in {"running", "processing"}:
        return "S3"
    if status == "failed":
        return "S4"
    return "S0"


def _approval_status(decision: dict[str, Any]) -> str:
    gate = str(decision.get("status_gate") or "PENDING").upper()
    if gate == "NEEDS_APPROVAL":
        return "REQUIRED"
    if gate == "PASS":
        return "APPROVED"
    if gate == "REJECTED":
        return "REJECTED"
    return "PENDING"


def projection_data_from_file(file_row: UploadFile) -> dict[str, Any]:
    meta = file_row.meta if isinstance(file_row.meta, dict) else {}
    decision = _decision_payload(file_row)
    rule_explanations = _as_list_of_str(decision.get("rule_explanations"))
    risk_flags = _as_list_of_str(decision.get("risk_flags"))

    part_count = meta.get("part_count")
    if not isinstance(part_count, int):
        part_count = meta.get("occurrence_count") if isinstance(meta.get("occurrence_count"), int) else None

    return {
        "latest_state": _latest_state(file_row, decision),
        "stage_progress": max(0, min(100, int(meta.get("progress_percent") or 0))),
        "decision_summary": (rule_explanations[0] if rule_explanations else None),
        "risk_summary": ", ".join(risk_flags[:6]) if risk_flags else None,
        "approval_status": _approval_status(decision),
        "status": str(file_row.status or "queued"),
        "kind": str(meta.get("kind") or ""),
        "mode": str(meta.get("mode") or ""),
        "part_count": part_count,
        "error_code": str(meta.get("error_code")) if meta.get("error_code") else None,
        "timestamps": {
            "created_at": file_row.created_at.isoformat() if isinstance(file_row.created_at, datetime) else None,
            "updated_at": file_row.updated_at.isoformat() if isinstance(file_row.updated_at, datetime) else None,
            "stage": str(meta.get("stage") or ""),
        },
        "payload_json": {
            "file_id": file_row.file_id,
            "status": str(file_row.status or "queued"),
            "progress": str(meta.get("progress") or ""),
            "progress_percent": max(0, min(100, int(meta.get("progress_percent") or 0))),
            "stage": str(meta.get("stage") or ""),
            "decision_json": decision,
            "risk_flags": risk_flags,
            "approval_required": bool(decision.get("approval_required")),
        },
    }


def upsert_projection(db: Session, file_row: UploadFile) -> FileReadProjection:
    data = projection_data_from_file(file_row)
    row = db.query(FileReadProjection).filter(FileReadProjection.file_id == file_row.file_id).first()
    if row is None:
        row = FileReadProjection(file_id=file_row.file_id)
        db.add(row)

    row.latest_state = data["latest_state"]
    row.stage_progress = data["stage_progress"]
    row.decision_summary = data["decision_summary"]
    row.risk_summary = data["risk_summary"]
    row.approval_status = data["approval_status"]
    row.status = data["status"]
    row.kind = data["kind"]
    row.mode = data["mode"]
    row.part_count = data["part_count"]
    row.error_code = data["error_code"]
    row.timestamps = data["timestamps"]
    row.payload_json = data["payload_json"]
    row.updated_at = datetime.utcnow()
    return row


def get_projection(db: Session, file_id: str) -> FileReadProjection | None:
    return db.query(FileReadProjection).filter(FileReadProjection.file_id == file_id).first()
