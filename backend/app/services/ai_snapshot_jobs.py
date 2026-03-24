from __future__ import annotations

import json
import socket
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from rq.job import Job
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.ai_learning import (
    AiCaseLog,
    AiSnapshotJob,
    BlockedCase,
    FailedCase,
    RecoveredCase,
    SolvedCase,
)
from app.queue import get_queue, redis_conn

SNAPSHOT_STATUS_DISABLED = "disabled"
SNAPSHOT_STATUS_QUEUED = "queued"
SNAPSHOT_STATUS_IN_PROGRESS = "in_progress"
SNAPSHOT_STATUS_RETRY_PENDING = "retry_pending"
SNAPSHOT_STATUS_UPLOADED = "uploaded"
SNAPSHOT_STATUS_FAILED = "failed"
SNAPSHOT_QUEUE_RESULT_TTL_SECONDS = 3600
SNAPSHOT_QUEUE_JOB_TTL_SECONDS = 24 * 3600
SNAPSHOT_ACTIVE_JOB_STATUSES = {"queued", "started", "scheduled", "deferred"}
MEMORY_MODELS = (SolvedCase, FailedCase, BlockedCase, RecoveredCase)


class SnapshotEnqueueError(RuntimeError):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_text(value: Any) -> str:
    return str(value or "").strip()


def _snapshot_relative_key(case_id: str, created_at: datetime) -> str:
    prefix = created_at.astimezone(timezone.utc).strftime("%Y/%m/%d")
    return f"{prefix}/{case_id}.json"


def _snapshot_local_path(relative_key: str) -> Path:
    return Path(settings.ai_memory_local_snapshot_dir) / relative_key


def _snapshot_drive_path(relative_key: str) -> str | None:
    if not settings.ai_memory_drive_enabled:
        return None
    drive_root = _safe_text(settings.ai_memory_drive_root)
    if not drive_root:
        return None
    return f"{drive_root.rstrip('/')}/{relative_key}"


def _relative_local_path(path: str | None) -> str | None:
    raw = _safe_text(path)
    if not raw:
        return None
    root = Path(settings.ai_memory_local_snapshot_dir)
    target = Path(raw)
    try:
        return str(target.relative_to(root))
    except ValueError:
        return target.name


def _relative_drive_path(path: str | None) -> str | None:
    raw = _safe_text(path)
    if not raw:
        return None
    root = _safe_text(settings.ai_memory_drive_root).rstrip("/")
    if root and raw.startswith(f"{root}/"):
        return raw[len(root) + 1 :]
    return raw


def _sync_memory_snapshot_state(db: Session, case_id: UUID, *, status: str, path: str | None, error: str | None) -> None:
    for model in MEMORY_MODELS:
        row = db.get(model, case_id)
        if row is None:
            continue
        outcome = row.outcome if isinstance(row.outcome, dict) else {}
        next_outcome = {
            **outcome,
            "drive_snapshot_status": status,
        }
        if path:
            next_outcome["drive_snapshot_path"] = path
        else:
            next_outcome.pop("drive_snapshot_path", None)
        if error:
            next_outcome["drive_snapshot_error"] = error
        else:
            next_outcome.pop("drive_snapshot_error", None)
        row.outcome = next_outcome
        db.add(row)


def sync_case_snapshot_state(
    db: Session,
    *,
    case_id: UUID,
    status: str,
    path: str | None,
    error: str | None,
) -> None:
    case_log = db.get(AiCaseLog, case_id)
    if case_log is None:
        return
    case_log.drive_snapshot_status = status
    case_log.drive_snapshot_path = path
    case_log.drive_snapshot_error = error
    db.add(case_log)
    _sync_memory_snapshot_state(db, case_id, status=status, path=path, error=error)


def write_local_snapshot(
    *,
    case_id: str,
    created_at: datetime,
    payload: dict[str, Any],
) -> tuple[str, str, str | None]:
    relative_key = _snapshot_relative_key(case_id, created_at)
    local_path = _snapshot_local_path(relative_key)
    local_path.parent.mkdir(parents=True, exist_ok=True)
    local_path.write_text(json.dumps(payload, ensure_ascii=True, sort_keys=True, indent=2), encoding="utf-8")
    return str(local_path), relative_key, _snapshot_drive_path(relative_key)


def create_snapshot_job(
    db: Session,
    *,
    case_log: AiCaseLog,
    local_snapshot_path: str,
    drive_target_path: str | None,
) -> AiSnapshotJob:
    job = (
        db.query(AiSnapshotJob)
        .filter(AiSnapshotJob.case_id == case_log.case_id)
        .order_by(AiSnapshotJob.created_at.desc())
        .first()
    )
    if job is None:
        job = AiSnapshotJob(
            case_id=case_log.case_id,
            tenant_id=case_log.tenant_id,
            idempotency_key=f"ai_case_snapshot:{case_log.case_id}",
        )
    job.local_snapshot_path = local_snapshot_path
    job.drive_target_path = drive_target_path
    job.upload_status = SNAPSHOT_STATUS_QUEUED if drive_target_path else SNAPSHOT_STATUS_DISABLED
    job.last_error = None
    job.next_retry_at = None
    job.locked_at = None
    job.locked_by = None
    db.add(job)
    db.flush()
    sync_case_snapshot_state(
        db,
        case_id=case_log.case_id,
        status=job.upload_status,
        path=None,
        error=None,
    )
    return job


def _queue_job_active(rq_job_id: str | None) -> bool:
    token = _safe_text(rq_job_id)
    if not token:
        return False
    try:
        job = Job.fetch(token, connection=redis_conn)
    except Exception:
        return False
    try:
        return job.get_status() in SNAPSHOT_ACTIVE_JOB_STATUSES
    except Exception:
        return False


def _queue_kwargs() -> dict[str, Any]:
    return {
        "job_timeout": settings.ai_snapshot_job_timeout_seconds + 30,
        "result_ttl": SNAPSHOT_QUEUE_RESULT_TTL_SECONDS,
        "ttl": SNAPSHOT_QUEUE_JOB_TTL_SECONDS,
    }


def enqueue_snapshot_upload_job(snapshot_job_id: UUID | str, *, db: Session | None = None) -> str:
    snapshot_uuid = UUID(str(snapshot_job_id))
    queue = get_queue(settings.ai_snapshot_queue_name)
    job = queue.enqueue(
        process_snapshot_upload_job,
        str(snapshot_uuid),
        job_id=f"ai_snapshot:{uuid4().hex}",
        **_queue_kwargs(),
    )
    managed_session = db is None
    session = db or SessionLocal()
    try:
        snapshot_job = session.get(AiSnapshotJob, snapshot_uuid)
        if snapshot_job is not None:
            snapshot_job.last_rq_job_id = job.get_id()
            snapshot_job.updated_at = _now()
            session.add(snapshot_job)
            if managed_session:
                session.commit()
            else:
                session.flush()
    finally:
        if managed_session:
            session.close()
    return job.get_id()


def _next_retry_at(attempt_count: int) -> datetime:
    delay = min(
        settings.ai_snapshot_retry_max_seconds,
        settings.ai_snapshot_retry_base_seconds * max(1, 2 ** max(attempt_count - 1, 0)),
    )
    return _now() + timedelta(seconds=delay)


def _claim_snapshot_job(db: Session, snapshot_job_id: UUID) -> AiSnapshotJob | None:
    now = _now()
    snapshot_job = (
        db.query(AiSnapshotJob)
        .filter(AiSnapshotJob.snapshot_job_id == snapshot_job_id)
        .with_for_update()
        .first()
    )
    if snapshot_job is None:
        return None
    if snapshot_job.upload_status == SNAPSHOT_STATUS_UPLOADED:
        return None
    if snapshot_job.upload_status == SNAPSHOT_STATUS_FAILED:
        return None
    if snapshot_job.upload_status == SNAPSHOT_STATUS_RETRY_PENDING and snapshot_job.next_retry_at and snapshot_job.next_retry_at > now:
        return None
    if snapshot_job.upload_status == SNAPSHOT_STATUS_IN_PROGRESS and snapshot_job.locked_at:
        lock_age = (now - snapshot_job.locked_at).total_seconds()
        if lock_age < settings.ai_snapshot_lock_timeout_seconds:
            return None
    snapshot_job.upload_status = SNAPSHOT_STATUS_IN_PROGRESS
    snapshot_job.attempt_count = int(snapshot_job.attempt_count or 0) + 1
    snapshot_job.locked_at = now
    snapshot_job.locked_by = socket.gethostname()
    snapshot_job.last_error = None
    snapshot_job.updated_at = now
    db.add(snapshot_job)
    sync_case_snapshot_state(
        db,
        case_id=snapshot_job.case_id,
        status=SNAPSHOT_STATUS_IN_PROGRESS,
        path=None,
        error=None,
    )
    db.commit()
    db.refresh(snapshot_job)
    return snapshot_job


def _mark_snapshot_uploaded(db: Session, snapshot_job: AiSnapshotJob) -> dict[str, Any]:
    now = _now()
    snapshot_job.upload_status = SNAPSHOT_STATUS_UPLOADED
    snapshot_job.last_error = None
    snapshot_job.next_retry_at = None
    snapshot_job.locked_at = None
    snapshot_job.locked_by = None
    snapshot_job.uploaded_at = now
    snapshot_job.updated_at = now
    db.add(snapshot_job)
    sync_case_snapshot_state(
        db,
        case_id=snapshot_job.case_id,
        status=SNAPSHOT_STATUS_UPLOADED,
        path=snapshot_job.drive_target_path,
        error=None,
    )
    db.commit()
    return {
        "snapshot_job_id": str(snapshot_job.snapshot_job_id),
        "case_id": str(snapshot_job.case_id),
        "upload_status": SNAPSHOT_STATUS_UPLOADED,
        "drive_target_path": snapshot_job.drive_target_path,
    }


def _mark_snapshot_failed(db: Session, snapshot_job: AiSnapshotJob, *, error: str) -> dict[str, Any]:
    attempts = int(snapshot_job.attempt_count or 0)
    terminal = attempts >= settings.ai_snapshot_max_attempts
    status = SNAPSHOT_STATUS_FAILED if terminal else SNAPSHOT_STATUS_RETRY_PENDING
    snapshot_job.upload_status = status
    snapshot_job.last_error = error
    snapshot_job.next_retry_at = None if terminal else _next_retry_at(attempts)
    snapshot_job.locked_at = None
    snapshot_job.locked_by = None
    snapshot_job.updated_at = _now()
    db.add(snapshot_job)
    sync_case_snapshot_state(
        db,
        case_id=snapshot_job.case_id,
        status=status,
        path=None,
        error=error,
    )
    db.commit()
    return {
        "snapshot_job_id": str(snapshot_job.snapshot_job_id),
        "case_id": str(snapshot_job.case_id),
        "upload_status": status,
        "last_error": error,
        "attempt_count": attempts,
        "next_retry_at": snapshot_job.next_retry_at.isoformat() if snapshot_job.next_retry_at else None,
    }


def mark_snapshot_retry_pending(
    snapshot_job_id: UUID | str,
    *,
    error: str,
    db: Session | None = None,
) -> dict[str, Any]:
    snapshot_uuid = UUID(str(snapshot_job_id))
    managed_session = db is None
    session = db or SessionLocal()
    try:
        snapshot_job = session.get(AiSnapshotJob, snapshot_uuid)
        if snapshot_job is None:
            raise ValueError("Snapshot job not found")
        snapshot_job.upload_status = SNAPSHOT_STATUS_RETRY_PENDING
        snapshot_job.last_error = error
        snapshot_job.next_retry_at = _now() + timedelta(seconds=settings.ai_snapshot_retry_base_seconds)
        snapshot_job.locked_at = None
        snapshot_job.locked_by = None
        snapshot_job.updated_at = _now()
        session.add(snapshot_job)
        sync_case_snapshot_state(
            session,
            case_id=snapshot_job.case_id,
            status=SNAPSHOT_STATUS_RETRY_PENDING,
            path=None,
            error=error,
        )
        if managed_session:
            session.commit()
        else:
            session.flush()
        return {
            "snapshot_job_id": str(snapshot_job.snapshot_job_id),
            "upload_status": SNAPSHOT_STATUS_RETRY_PENDING,
            "last_error": error,
            "next_retry_at": snapshot_job.next_retry_at.isoformat() if snapshot_job.next_retry_at else None,
        }
    finally:
        if managed_session:
            session.close()


def _upload_snapshot_file(local_snapshot_path: str, drive_target_path: str) -> None:
    remote_dir = drive_target_path.rsplit("/", 1)[0]
    subprocess.run(
        ["rclone", "mkdir", remote_dir],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    subprocess.run(
        ["rclone", "copyto", "--ignore-existing", local_snapshot_path, drive_target_path],
        check=True,
        capture_output=True,
        text=True,
        timeout=settings.ai_snapshot_job_timeout_seconds,
    )


def process_snapshot_upload_job(snapshot_job_id: str) -> dict[str, Any]:
    snapshot_uuid = UUID(str(snapshot_job_id))
    db = SessionLocal()
    try:
        snapshot_job = _claim_snapshot_job(db, snapshot_uuid)
        if snapshot_job is None:
            return {"snapshot_job_id": str(snapshot_uuid), "status": "skipped"}

        local_path = Path(snapshot_job.local_snapshot_path)
        drive_target = _safe_text(snapshot_job.drive_target_path)
        if not drive_target:
            return _mark_snapshot_failed(db, snapshot_job, error="drive target path missing")
        if not local_path.exists():
            return _mark_snapshot_failed(db, snapshot_job, error="local snapshot missing")

        try:
            _upload_snapshot_file(str(local_path), drive_target)
        except FileNotFoundError:
            return _mark_snapshot_failed(db, snapshot_job, error="rclone not available in worker runtime")
        except subprocess.CalledProcessError as exc:
            stderr = _safe_text(exc.stderr) or _safe_text(exc.stdout) or "rclone copy failed"
            return _mark_snapshot_failed(db, snapshot_job, error=stderr)
        except subprocess.TimeoutExpired:
            return _mark_snapshot_failed(db, snapshot_job, error="rclone timed out")

        return _mark_snapshot_uploaded(db, snapshot_job)
    finally:
        db.close()


def enqueue_due_snapshot_jobs(limit: int = 25) -> dict[str, Any]:
    now = _now()
    db = SessionLocal()
    enqueued = 0
    recovered = 0
    try:
        stale_jobs = (
            db.query(AiSnapshotJob)
            .filter(
                AiSnapshotJob.upload_status == SNAPSHOT_STATUS_IN_PROGRESS,
                AiSnapshotJob.locked_at.is_not(None),
                AiSnapshotJob.locked_at <= now - timedelta(seconds=settings.ai_snapshot_lock_timeout_seconds),
            )
            .all()
        )
        for snapshot_job in stale_jobs:
            snapshot_job.upload_status = SNAPSHOT_STATUS_RETRY_PENDING
            snapshot_job.last_error = _safe_text(snapshot_job.last_error) or "stale in-progress lock expired"
            snapshot_job.next_retry_at = now
            snapshot_job.locked_at = None
            snapshot_job.locked_by = None
            snapshot_job.updated_at = now
            db.add(snapshot_job)
            sync_case_snapshot_state(
                db,
                case_id=snapshot_job.case_id,
                status=SNAPSHOT_STATUS_RETRY_PENDING,
                path=None,
                error=snapshot_job.last_error,
            )
            recovered += 1
        if recovered:
            db.commit()

        due_jobs = (
            db.query(AiSnapshotJob)
            .filter(
                AiSnapshotJob.upload_status.in_((SNAPSHOT_STATUS_QUEUED, SNAPSHOT_STATUS_RETRY_PENDING)),
                or_(AiSnapshotJob.next_retry_at.is_(None), AiSnapshotJob.next_retry_at <= now),
            )
            .order_by(AiSnapshotJob.created_at.asc())
            .limit(limit)
            .all()
        )
        for snapshot_job in due_jobs:
            if _queue_job_active(snapshot_job.last_rq_job_id):
                continue
            try:
                enqueue_snapshot_upload_job(snapshot_job.snapshot_job_id, db=db)
            except Exception as exc:
                snapshot_job.upload_status = SNAPSHOT_STATUS_RETRY_PENDING
                snapshot_job.last_error = f"queue enqueue failed: {exc}"
                snapshot_job.next_retry_at = _now() + timedelta(seconds=settings.ai_snapshot_retry_base_seconds)
                snapshot_job.updated_at = _now()
                db.add(snapshot_job)
                sync_case_snapshot_state(
                    db,
                    case_id=snapshot_job.case_id,
                    status=SNAPSHOT_STATUS_RETRY_PENDING,
                    path=None,
                    error=snapshot_job.last_error,
                )
                db.commit()
                continue
            db.commit()
            enqueued += 1
        return {"enqueued": enqueued, "recovered_stale_locks": recovered}
    finally:
        db.close()


def list_snapshot_jobs(db: Session, *, status: str | None = None, limit: int = 50) -> dict[str, Any]:
    query = db.query(AiSnapshotJob, AiCaseLog).join(AiCaseLog, AiCaseLog.case_id == AiSnapshotJob.case_id)
    token = _safe_text(status).lower()
    if token:
        query = query.filter(AiSnapshotJob.upload_status == token)
    rows = query.order_by(AiSnapshotJob.created_at.desc()).limit(limit).all()
    items = []
    for snapshot_job, case_log in rows:
        items.append(
            {
                "snapshot_job_id": str(snapshot_job.snapshot_job_id),
                "case_id": str(snapshot_job.case_id),
                "tenant_id": int(snapshot_job.tenant_id),
                "file_id": case_log.file_id,
                "run_type": case_log.run_type,
                "final_status": case_log.final_status,
                "upload_status": snapshot_job.upload_status,
                "attempt_count": int(snapshot_job.attempt_count or 0),
                "last_error": snapshot_job.last_error,
                "next_retry_at": snapshot_job.next_retry_at.isoformat() if snapshot_job.next_retry_at else None,
                "uploaded_at": snapshot_job.uploaded_at.isoformat() if snapshot_job.uploaded_at else None,
                "drive_target_key": _relative_drive_path(snapshot_job.drive_target_path),
                "local_snapshot_key": _relative_local_path(snapshot_job.local_snapshot_path),
                "created_at": snapshot_job.created_at.isoformat() if snapshot_job.created_at else None,
                "updated_at": snapshot_job.updated_at.isoformat() if snapshot_job.updated_at else None,
            }
        )
    return {"items": items, "total": len(items), "status": token or "all"}


def get_snapshot_job_stats(db: Session) -> dict[str, Any]:
    counts = {
        "disabled": db.query(func.count(AiSnapshotJob.snapshot_job_id)).filter(AiSnapshotJob.upload_status == SNAPSHOT_STATUS_DISABLED).scalar() or 0,
        "queued": db.query(func.count(AiSnapshotJob.snapshot_job_id)).filter(AiSnapshotJob.upload_status == SNAPSHOT_STATUS_QUEUED).scalar() or 0,
        "in_progress": db.query(func.count(AiSnapshotJob.snapshot_job_id)).filter(AiSnapshotJob.upload_status == SNAPSHOT_STATUS_IN_PROGRESS).scalar() or 0,
        "retry_pending": db.query(func.count(AiSnapshotJob.snapshot_job_id)).filter(AiSnapshotJob.upload_status == SNAPSHOT_STATUS_RETRY_PENDING).scalar() or 0,
        "failed": db.query(func.count(AiSnapshotJob.snapshot_job_id)).filter(AiSnapshotJob.upload_status == SNAPSHOT_STATUS_FAILED).scalar() or 0,
        "uploaded": db.query(func.count(AiSnapshotJob.snapshot_job_id)).filter(AiSnapshotJob.upload_status == SNAPSHOT_STATUS_UPLOADED).scalar() or 0,
    }
    oldest_pending = (
        db.query(AiSnapshotJob)
        .filter(AiSnapshotJob.upload_status.in_((SNAPSHOT_STATUS_QUEUED, SNAPSHOT_STATUS_RETRY_PENDING, SNAPSHOT_STATUS_IN_PROGRESS)))
        .order_by(AiSnapshotJob.created_at.asc())
        .first()
    )
    queue_depth = 0
    started_count = 0
    try:
        queue = get_queue(settings.ai_snapshot_queue_name)
        queue_depth = queue.count
        started_count = queue.started_job_registry.count
    except Exception:
        queue_depth = 0
        started_count = 0
    return {
        **counts,
        "queue_name": settings.ai_snapshot_queue_name,
        "queue_depth": queue_depth,
        "started_count": started_count,
        "oldest_pending_age_seconds": (
            max(int((_now() - oldest_pending.created_at).total_seconds()), 0)
            if oldest_pending is not None and oldest_pending.created_at is not None
            else None
        ),
    }


def retry_snapshot_job(db: Session, *, snapshot_job_id: str) -> dict[str, Any]:
    snapshot_uuid = UUID(str(snapshot_job_id))
    snapshot_job = db.get(AiSnapshotJob, snapshot_uuid)
    if snapshot_job is None:
        raise ValueError("Snapshot job not found")
    if snapshot_job.upload_status == SNAPSHOT_STATUS_DISABLED or not _safe_text(snapshot_job.drive_target_path):
        return {
            "snapshot_job_id": str(snapshot_job.snapshot_job_id),
            "upload_status": SNAPSHOT_STATUS_DISABLED,
            "requeued": False,
        }
    if snapshot_job.upload_status == SNAPSHOT_STATUS_UPLOADED:
        return {
            "snapshot_job_id": str(snapshot_job.snapshot_job_id),
            "upload_status": SNAPSHOT_STATUS_UPLOADED,
            "requeued": False,
        }

    snapshot_job.upload_status = SNAPSHOT_STATUS_QUEUED
    snapshot_job.last_error = None
    snapshot_job.next_retry_at = None
    snapshot_job.locked_at = None
    snapshot_job.locked_by = None
    snapshot_job.updated_at = _now()
    db.add(snapshot_job)
    sync_case_snapshot_state(
        db,
        case_id=snapshot_job.case_id,
        status=SNAPSHOT_STATUS_QUEUED,
        path=None,
        error=None,
    )
    db.commit()

    try:
        rq_job_id = enqueue_snapshot_upload_job(snapshot_job.snapshot_job_id)
    except Exception as exc:
        snapshot_job = db.get(AiSnapshotJob, snapshot_uuid)
        if snapshot_job is not None:
            mark_snapshot_retry_pending(
                snapshot_job.snapshot_job_id,
                error=f"queue enqueue failed: {exc}",
                db=db,
            )
            db.commit()
        raise SnapshotEnqueueError(str(exc))

    refreshed = db.get(AiSnapshotJob, snapshot_uuid)
    return {
        "snapshot_job_id": str(snapshot_uuid),
        "upload_status": refreshed.upload_status if refreshed is not None else SNAPSHOT_STATUS_QUEUED,
        "last_rq_job_id": refreshed.last_rq_job_id if refreshed is not None else rq_job_id,
        "requeued": True,
    }


def backfill_legacy_snapshot_jobs(limit: int = 200) -> int:
    db = SessionLocal()
    created = 0
    try:
        pending_rows = (
            db.query(AiCaseLog)
            .outerjoin(AiSnapshotJob, AiSnapshotJob.case_id == AiCaseLog.case_id)
            .filter(
                AiSnapshotJob.snapshot_job_id.is_(None),
                AiCaseLog.drive_snapshot_status.in_(("local_only", SNAPSHOT_STATUS_FAILED, SNAPSHOT_STATUS_QUEUED, SNAPSHOT_STATUS_RETRY_PENDING)),
            )
            .order_by(AiCaseLog.created_at.asc())
            .limit(limit)
            .all()
        )
        for case_log in pending_rows:
            created_at = case_log.created_at or _now()
            relative_key = _snapshot_relative_key(str(case_log.case_id), created_at)
            local_path = _snapshot_local_path(relative_key)
            if not local_path.exists():
                continue
            drive_target = _snapshot_drive_path(relative_key)
            if not drive_target:
                continue
            snapshot_job = AiSnapshotJob(
                case_id=case_log.case_id,
                tenant_id=case_log.tenant_id,
                idempotency_key=f"ai_case_snapshot:{case_log.case_id}",
                local_snapshot_path=str(local_path),
                drive_target_path=drive_target,
                upload_status=SNAPSHOT_STATUS_QUEUED,
                attempt_count=0,
            )
            db.add(snapshot_job)
            sync_case_snapshot_state(
                db,
                case_id=case_log.case_id,
                status=SNAPSHOT_STATUS_QUEUED,
                path=None,
                error=case_log.drive_snapshot_error,
            )
            created += 1
        if created:
            db.commit()
        return created
    finally:
        db.close()
