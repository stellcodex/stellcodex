from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from rq.job import Job
from sqlalchemy.orm import Session

from app.core.ids import normalize_scx_id
from app.core.format_registry import get_rule_for_filename
from app.db.session import get_db
from app.models.file import UploadFile
from app.models.job_failure import JobFailure
from app.models.orchestrator import OrchestratorSession
from app.queue import redis_conn
from app.security.deps import Principal, get_current_principal

router = APIRouter(tags=["jobs"])


class JobStatusOut(BaseModel):
    job_id: str
    status: str
    enqueued_at: datetime | None
    started_at: datetime | None
    ended_at: datetime | None
    origin: str | None
    timeout: int | None
    meta: dict | None
    result: str | None
    error: str | None


class JobEnqueueOut(BaseModel):
    job_id: str


class RecentJobOut(BaseModel):
    file_id: str
    job_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    error_code: str | None = None


def _short_exc(exc_info: str | None) -> str | None:
    if not exc_info:
        return None
    lines = [line for line in exc_info.splitlines() if line.strip()]
    return lines[-1] if lines else None


def _safe_meta(payload: dict | None) -> dict | None:
    if not isinstance(payload, dict):
        return None
    redacted: dict[str, object] = {}
    blocked_tokens = {"storage_key", "object_key", "bucket", "path", "provider", "secret", "token"}
    for key, value in payload.items():
        lowered = str(key).lower()
        if any(token in lowered for token in blocked_tokens):
            continue
        redacted[str(key)] = value
    return redacted or None


def _scope_uploads(db: Session, principal: Principal):
    if principal.typ == "guest":
        owner_sub = principal.owner_sub or ""
        return db.query(UploadFile).filter(
            (UploadFile.owner_anon_sub == owner_sub) | (UploadFile.owner_sub == owner_sub)
        )
    return db.query(UploadFile).filter(UploadFile.owner_user_id == principal.user_id)


def _recent_status(row: UploadFile) -> str:
    token = str(row.status or "").strip().lower()
    if token in {"pending", "queued"}:
        return "queued"
    if token in {"processing", "running"}:
        return "running"
    if token in {"ready", "succeeded"}:
        return "succeeded"
    if token == "failed":
        return "failed"
    return "queued"


def _recent_job_type(row: UploadFile, session: OrchestratorSession | None) -> str:
    meta = row.meta if isinstance(row.meta, dict) else {}
    rule = get_rule_for_filename(row.original_filename or "")
    kind = str(meta.get("kind") or (rule.kind if rule else "other"))
    if isinstance(meta.get("dfm_findings"), dict):
        return "dfm"
    if session is not None and str(session.state or "") in {"S4", "S5", "S6", "S7"}:
        return "orchestrate"
    if kind == "archive":
        return "pack"
    if kind in {"3d", "2d", "doc", "image"}:
        return "convert"
    return "other"


def _failure_code(row: JobFailure | None) -> str | None:
    if row is None:
        return None
    parts = [str(row.stage or "").strip(), str(row.error_class or "").strip()]
    token = "_".join(part for part in parts if part).upper()
    return token or None


def _public_file_id(value: str) -> str:
    try:
        return normalize_scx_id(value)
    except ValueError:
        return value


def _as_utc(dt: datetime | None) -> datetime:
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@router.post("/ping", response_model=JobEnqueueOut)
def enqueue_ping():
    from app.workers.tasks import enqueue_ping_job

    job_id = enqueue_ping_job()
    return JobEnqueueOut(job_id=job_id)


@router.get("/recent", response_model=list[RecentJobOut])
def recent_jobs(
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    rows = (
        _scope_uploads(db, principal)
        .order_by(UploadFile.updated_at.desc(), UploadFile.created_at.desc())
        .limit(limit)
        .all()
    )
    file_ids = [row.file_id for row in rows]
    sessions = (
        db.query(OrchestratorSession)
        .filter(OrchestratorSession.file_id.in_(file_ids))
        .all()
        if file_ids
        else []
    )
    failures = (
        db.query(JobFailure)
        .filter(JobFailure.file_id.in_(file_ids))
        .order_by(JobFailure.created_at.desc())
        .all()
        if file_ids
        else []
    )

    session_by_file = {row.file_id: row for row in sessions}
    latest_failure_by_file: dict[str, JobFailure] = {}
    for row in failures:
        if row.file_id and row.file_id not in latest_failure_by_file:
            latest_failure_by_file[row.file_id] = row

    items: list[RecentJobOut] = []
    for row in rows:
        session = session_by_file.get(row.file_id)
        failure = latest_failure_by_file.get(row.file_id)
        created_at = _as_utc(row.created_at)
        updated_at = _as_utc(row.updated_at)
        session_updated_at = _as_utc(session.updated_at) if session is not None else None
        failure_created_at = _as_utc(failure.created_at) if failure is not None else None
        if session_updated_at is not None and session_updated_at > updated_at:
            updated_at = session_updated_at
        if failure_created_at is not None and failure_created_at > updated_at:
            updated_at = failure_created_at
        items.append(
            RecentJobOut(
                file_id=_public_file_id(row.file_id),
                job_type=_recent_job_type(row, session),
                status=_recent_status(row),
                created_at=created_at,
                updated_at=updated_at,
                error_code=_failure_code(failure),
            )
        )
    items.sort(key=lambda item: item.updated_at, reverse=True)
    return items


@router.get("/{job_id}", response_model=JobStatusOut)
def get_job(job_id: str):
    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception:
        raise HTTPException(status_code=404, detail="Job not found")

    result = None
    if job.result is not None:
        try:
            result = str(job.result)
        except Exception:
            result = "<unserializable>"

    return JobStatusOut(
        job_id=job.id,
        status=job.get_status(),
        enqueued_at=job.enqueued_at,
        started_at=job.started_at,
        ended_at=job.ended_at,
        origin=job.origin,
        timeout=job.timeout,
        meta=_safe_meta(job.meta),
        result=result,
        error=_short_exc(job.exc_info),
    )
