from __future__ import annotations

import copy
import json
import uuid
from secrets import compare_digest
from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.format_registry import get_rule_for_filename
from app.core.ids import format_scx_file_id, normalize_scx_file_id, normalize_scx_id
from app.core.storage import get_s3_client
from app.db.session import get_db
from app.models.file import UploadFile as UploadFileModel
from app.models.orchestrator import OrchestratorSession
from app.models.share import Share
from app.services.ai_learning import (
    SnapshotEnqueueError,
    get_memory_context,
    record_case_run,
    search_experience_entries,
    store_decision_log,
    store_experience_entry,
)
from app.services.rule_configs import RuleConfigMissingError, load_hybrid_v1_config

class InternalSessionUpsertIn(BaseModel):
    session_id: str | None = None
    file_id: str = Field(min_length=4, max_length=64)
    state: str = Field(default="S0", max_length=8)
    state_code: str = Field(default="S0", max_length=8)
    state_label: str = Field(default="Uploaded", max_length=64)
    status_gate: str = Field(default="PASS", max_length=32)
    approval_required: bool = False
    rule_version: str = Field(default="v0.0", max_length=32)
    mode: str = Field(default="visual_only", max_length=32)
    confidence: float = 0.0
    risk_flags: list[str] = Field(default_factory=list)
    decision_json: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None


class InternalAiCaseLogIn(BaseModel):
    case_id: str | None = None
    file_id: str = Field(min_length=4, max_length=64)
    session_id: str | None = Field(default=None, max_length=64)
    run_type: str = Field(min_length=2, max_length=48)
    input_payload: dict[str, Any] = Field(default_factory=dict)
    decision_output: dict[str, Any] = Field(default_factory=dict)
    execution_trace: list[dict[str, Any]] = Field(default_factory=list)
    final_status: str = Field(min_length=6, max_length=16)
    error_trace: dict[str, Any] | None = None
    duration_ms: int = Field(default=0, ge=0)
    timestamp: datetime | None = None
    retrieved_context_summary: dict[str, Any] | None = None


class InternalAiMemoryContextIn(BaseModel):
    file_id: str = Field(min_length=4, max_length=64)
    project_id: str | None = Field(default=None, max_length=128)
    mode: str | None = Field(default=None, max_length=48)
    geometry_meta: dict[str, Any] | None = None
    dfm_findings: dict[str, Any] | None = None


class InternalAiExperienceWriteIn(BaseModel):
    task_query: str = Field(min_length=2, max_length=500)
    successful_plan: dict[str, Any] = Field(default_factory=dict)
    lessons_learned: str | None = Field(default=None, max_length=4000)
    feedback_from_owner: str | None = Field(default=None, max_length=4000)


class InternalAiExperienceSearchIn(BaseModel):
    query: str = Field(min_length=2, max_length=240)
    limit: int = Field(default=5, ge=1, le=20)


class InternalAiDecisionLogIn(BaseModel):
    prompt: str = Field(min_length=2, max_length=500)
    lane: str = Field(min_length=2, max_length=64)
    executor: str = Field(min_length=2, max_length=128)
    decision_json: dict[str, Any] = Field(default_factory=dict)


def _require_internal_token(x_internal_token: str | None = Header(default=None, alias="X-Internal-Token")) -> None:
    expected = str(settings.bootstrap_admin_token or "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="Internal runtime token is not configured")
    provided = str(x_internal_token or "").strip()
    if not provided or not compare_digest(provided, expected):
        raise HTTPException(status_code=403, detail="Forbidden")




router = APIRouter(
    prefix="/internal/runtime",
    tags=["internal-runtime"],
    dependencies=[Depends(_require_internal_token)],
)


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


def _rule_hint(file_row: UploadFileModel) -> tuple[str | None, str | None]:
    meta = file_row.meta if isinstance(file_row.meta, dict) else {}
    rule = get_rule_for_filename(file_row.original_filename or "")
    kind = str(meta.get("kind") or (rule.kind if rule else "")) or None
    mode = str(meta.get("mode") or (rule.mode if rule else "")) or None
    return kind, mode


def _load_assembly_tree(file_row: UploadFileModel, meta: dict[str, Any]) -> list[dict[str, Any]] | None:
    tree = meta.get("assembly_tree")
    if isinstance(tree, list):
        return [node for node in tree if isinstance(node, dict)]
    key = meta.get("assembly_meta_key")
    if not isinstance(key, str) or not key:
        return None
    try:
        s3 = get_s3_client(settings)
        obj = s3.get_object(Bucket=file_row.bucket, Key=key)
        payload = json.loads(obj["Body"].read().decode("utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    occurrences = payload.get("occurrences")
    if not isinstance(occurrences, list):
        return None
    return [node for node in occurrences if isinstance(node, dict)]


def _active_share_exists(db: Session, file_id: str) -> bool:
    now = datetime.utcnow()
    share = (
        db.query(Share)
        .filter(
            Share.file_id == file_id,
            Share.revoked_at.is_(None),
            Share.expires_at > now,
        )
        .order_by(Share.created_at.desc())
        .first()
    )
    return share is not None


def _serialize_session(session: OrchestratorSession) -> dict[str, Any]:
    return {
        "session_id": str(session.id),
        "file_id": _public_file_id(session.file_id),
        "state": session.state,
        "state_code": session.state_code,
        "state_label": session.state_label,
        "status_gate": session.status_gate,
        "approval_required": bool(session.approval_required),
        "rule_version": session.rule_version,
        "mode": session.mode,
        "confidence": float(session.confidence or 0.0),
        "risk_flags": [str(item) for item in (session.risk_flags or []) if str(item or "").strip()],
        "decision_json": session.decision_json if isinstance(session.decision_json, dict) else {},
        "notes": session.notes,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
    }


def _file_context(db: Session, file_row: UploadFileModel, *, include_assembly_tree: bool) -> dict[str, Any]:
    meta = copy.deepcopy(file_row.meta if isinstance(file_row.meta, dict) else {})
    if include_assembly_tree and "assembly_tree" not in meta:
        tree = _load_assembly_tree(file_row, meta)
        if isinstance(tree, list):
            meta["assembly_tree"] = tree
    kind, mode = _rule_hint(file_row)
    return {
        "file_id": _public_file_id(file_row.file_id),
        "canonical_file_id": file_row.file_id,
        "tenant_id": int(file_row.tenant_id),
        "original_filename": file_row.original_filename,
        "content_type": file_row.content_type,
        "status": file_row.status,
        "size_bytes": int(file_row.size_bytes),
        "bucket": file_row.bucket,
        "object_key": file_row.object_key,
        "gltf_key": file_row.gltf_key,
        "thumbnail_key": file_row.thumbnail_key,
        "kind": kind,
        "mode": mode,
        "project_id": str(meta.get("project_id") or "default"),
        "rule_version": str(meta.get("rule_version") or ""),
        "meta": meta,
        "decision_json": file_row.decision_json if isinstance(file_row.decision_json, dict) else {},
        "active_share_exists": _active_share_exists(db, file_row.file_id),
    }


@router.get("/files/{file_id}/context")
def get_file_context(
    file_id: str,
    include_assembly_tree: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    file_row = _get_file_by_identifier(db, file_id)
    if file_row is None:
        raise HTTPException(status_code=404, detail="File not found")
    return _file_context(db, file_row, include_assembly_tree=include_assembly_tree)


@router.get("/rule-config")
def get_rule_config(
    project_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    try:
        config, version = load_hybrid_v1_config(db, project_id=project_id)
    except RuleConfigMissingError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return {
        "project_id": str(project_id or "default"),
        "rule_version": version,
        "config": config,
    }


@router.get("/orchestrator/sessions/by-file/{file_id}")
def get_session_by_file(file_id: str, db: Session = Depends(get_db)):
    file_row = _get_file_by_identifier(db, file_id)
    if file_row is None:
        raise HTTPException(status_code=404, detail="File not found")
    session = db.query(OrchestratorSession).filter(OrchestratorSession.file_id == file_row.file_id).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return _serialize_session(session)


@router.get("/orchestrator/sessions/by-id/{session_id}")
def get_session_by_id(session_id: str, db: Session = Depends(get_db)):
    try:
        session_uuid = UUID(str(session_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session id")
    session = db.query(OrchestratorSession).filter(OrchestratorSession.id == session_uuid).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return _serialize_session(session)


@router.post("/orchestrator/sessions/upsert")
def upsert_session(data: InternalSessionUpsertIn, db: Session = Depends(get_db)):
    file_row = _get_file_by_identifier(db, data.file_id)
    if file_row is None:
        raise HTTPException(status_code=404, detail="File not found")

    session: OrchestratorSession | None = None
    if data.session_id:
        try:
            session_uuid = UUID(str(data.session_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid session id")
        session = db.query(OrchestratorSession).filter(OrchestratorSession.id == session_uuid).first()
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = db.query(OrchestratorSession).filter(OrchestratorSession.file_id == file_row.file_id).first()

    if session is None:
        session = OrchestratorSession(id=uuid.uuid4(), file_id=file_row.file_id)
        db.add(session)
        db.flush()

    session.file_id = file_row.file_id
    session.state = str(data.state)
    session.state_code = str(data.state_code)
    session.state_label = str(data.state_label)
    session.status_gate = str(data.status_gate)
    session.approval_required = bool(data.approval_required)
    session.rule_version = str(data.rule_version)
    session.mode = str(data.mode)
    session.confidence = float(data.confidence or 0.0)
    session.risk_flags = [str(item) for item in data.risk_flags if str(item or "").strip()]
    session.decision_json = data.decision_json if isinstance(data.decision_json, dict) else {}
    session.notes = data.notes

    db.add(session)
    db.commit()
    db.refresh(session)
    return _serialize_session(session)


@router.post("/ai/cases/log")
def log_ai_case(data: InternalAiCaseLogIn, db: Session = Depends(get_db)):
    file_row = _get_file_by_identifier(db, data.file_id)
    if file_row is None:
        raise HTTPException(status_code=404, detail="File not found")
    try:
        return record_case_run(
            db,
            file_row=file_row,
            case_id=data.case_id,
            session_id=data.session_id,
            run_type=data.run_type,
            input_payload=data.input_payload,
            decision_output=data.decision_output,
            execution_trace=data.execution_trace,
            final_status=data.final_status,
            error_trace=data.error_trace,
            duration_ms=data.duration_ms,
            timestamp=data.timestamp,
            retrieved_context_summary=data.retrieved_context_summary,
        )
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))
    except SnapshotEnqueueError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=str(exc))


@router.post("/ai/memory/context")
def ai_memory_context(data: InternalAiMemoryContextIn, db: Session = Depends(get_db)):
    file_row = _get_file_by_identifier(db, data.file_id)
    if file_row is None:
        raise HTTPException(status_code=404, detail="File not found")
    return get_memory_context(
        db,
        file_row=file_row,
        project_id=data.project_id,
        mode=data.mode,
        geometry_meta=data.geometry_meta,
        dfm_findings=data.dfm_findings,
    )


@router.post("/ai/experience/write")
def ai_experience_write(data: InternalAiExperienceWriteIn, db: Session = Depends(get_db)):
    return store_experience_entry(
        db,
        task_query=data.task_query,
        successful_plan=data.successful_plan,
        lessons_learned=data.lessons_learned,
        feedback_from_owner=data.feedback_from_owner,
    )


@router.post("/ai/experience/search")
def ai_experience_search(data: InternalAiExperienceSearchIn, db: Session = Depends(get_db)):
    return search_experience_entries(db, query=data.query, limit=data.limit)


@router.post("/ai/decision-log")
def ai_decision_log(data: InternalAiDecisionLogIn, db: Session = Depends(get_db)):
    return store_decision_log(
        db,
        prompt=data.prompt,
        lane=data.lane,
        executor=data.executor,
        decision_json=data.decision_json,
    )
