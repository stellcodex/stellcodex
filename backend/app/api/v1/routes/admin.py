from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from rq import Worker
from rq.registry import FailedJobRegistry, StartedJobRegistry
from sqlalchemy import desc, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.ids import normalize_scx_id
from app.core.storage import get_s3_client
from app.db.session import get_db
from app.models.audit import AuditEvent
from app.models.file import UploadFile
from app.models.job_failure import JobFailure
from app.models.orchestrator import OrchestratorSession
from app.models.share import Share
from app.models.user import RevokedToken, User
from app.queue import get_queue, redis_conn
from app.security.deps import require_role, Principal
from app.security.jwt import create_user_token
from app.services.audit import log_event
from app.services.orchestra_client import proxy_orchestra

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_role("admin"))])

QUEUE_NAMES = ["cad", "drawing", "render"]


class IssueTokenIn(BaseModel):
    ttl_minutes: int = Field(default=7 * 24 * 60, ge=30, le=30 * 24 * 60)


class RevokeSessionsIn(BaseModel):
    jtis: list[str] | None = None
    reason: str | None = None


class AdminApprovalIn(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _failure_code(stage: str | None, error_class: str | None) -> str | None:
    parts = [str(stage or "").strip(), str(error_class or "").strip()]
    token = "_".join(part for part in parts if part).upper()
    return token or None


def _safe_meta_preview(data: dict | None) -> dict | None:
    if not isinstance(data, dict):
        return None
    blocked_tokens = {"storage_key", "object_key", "bucket", "path", "provider", "secret", "token"}
    preview: dict[str, object] = {}
    for key, value in data.items():
        lowered = str(key).lower()
        if any(token in lowered for token in blocked_tokens):
            continue
        if isinstance(value, str) and len(value) > 240:
            preview[str(key)] = f"{value[:237]}..."
            continue
        preview[str(key)] = value
    return preview or None


def _public_file_id(value: str | None) -> str | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        return normalize_scx_id(raw)
    except ValueError:
        return raw


def _approval_payload(session: OrchestratorSession, file_row: UploadFile | None) -> dict:
    decision_json = session.decision_json if isinstance(session.decision_json, dict) else {}
    flags = session.risk_flags if isinstance(session.risk_flags, list) else decision_json.get("conflict_flags")
    return {
        "id": str(session.id),
        "file_id": _public_file_id(session.file_id),
        "filename": file_row.original_filename if file_row is not None else None,
        "file_status": file_row.status if file_row is not None else None,
        "state": session.state,
        "state_label": session.state_label or session.state,
        "approval_required": bool(session.approval_required),
        "risk_flags": [str(item) for item in flags] if isinstance(flags, list) else [],
        "decision_json": decision_json,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
    }


def _approval_session_or_404(db: Session, approval_id: str) -> OrchestratorSession:
    try:
        approval_uuid = UUID(approval_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid approval id")
    session = db.query(OrchestratorSession).filter(OrchestratorSession.id == approval_uuid).first()
    if session is None:
        raise HTTPException(status_code=404, detail="Approval not found")
    return session


@router.get("/health")
def admin_health(db: Session = Depends(get_db)):
    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    redis_ok = False
    try:
        if settings.redis_url:
            redis_ok = bool(redis_conn.ping())
    except Exception:
        redis_ok = False

    storage_ok = None
    if settings.s3_enabled:
        try:
            s3 = get_s3_client(settings)
            s3.head_bucket(Bucket=settings.s3_bucket)
            storage_ok = True
        except Exception:
            storage_ok = False

    queue_depth = 0
    worker_ok = False
    if redis_ok:
        try:
            queue_depth = sum(get_queue(name).count for name in QUEUE_NAMES)
            worker_ok = bool(Worker.all(connection=redis_conn))
        except Exception:
            worker_ok = False

    payload = {
        "api": "ok",
        "db": "ok" if db_ok else "fail",
        "redis": "ok" if redis_ok else "fail",
        "rq": "ok" if redis_ok else "fail",
        "worker": "ok" if worker_ok else "fail",
        "queue_depth": queue_depth,
        "failed_jobs": int(db.query(JobFailure).count()),
        "checked_at": _now(),
    }
    if storage_ok is not None:
        payload["storage"] = "ok" if storage_ok else "fail"
    return payload


@router.get("/queues")
def admin_queues():
    if not settings.redis_url:
        raise HTTPException(status_code=503, detail="Redis not configured")

    queues = []
    for name in QUEUE_NAMES:
        q = get_queue(name)
        started = StartedJobRegistry(queue=q)
        failed = FailedJobRegistry(queue=q)
        queues.append(
            {
                "name": name,
                "queued_count": q.count,
                "started_count": started.count,
                "failed_count": failed.count,
            }
        )
    return {"queues": queues, "queue_depth": sum(item["queued_count"] for item in queues), "checked_at": _now()}


@router.get("/queues/failed")
def admin_failed_jobs(limit: int = 50, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 200))
    rows: List[JobFailure] = (
        db.query(JobFailure)
        .order_by(desc(JobFailure.created_at))
        .limit(limit)
        .all()
    )
    return {
        "items": [
            {
                "id": str(r.id),
                "job_id": r.job_id,
                "file_id": _public_file_id(r.file_id),
                "type": r.stage,
                "status": "failed",
                "stage": r.stage,
                "failure_code": _failure_code(r.stage, r.error_class),
                "error_class": r.error_class,
                "message": (r.message or "")[:300],
                "safe_message": (r.message or "")[:300],
                "created_at": r.created_at,
                "updated_at": r.created_at,
            }
            for r in rows
        ]
    }


@router.get("/failures")
def admin_failures_alias(limit: int = 50, db: Session = Depends(get_db)):
    # Backward-compatible alias kept for existing admin clients.
    return admin_failed_jobs(limit=limit, db=db)


@router.get("/users")
def admin_users(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).limit(200).all()
    return {
        "items": [
            {
                "id": str(u.id),
                "email": u.email,
                "role": u.role,
                "is_suspended": u.is_suspended,
                "created_at": u.created_at,
            }
            for u in users
        ]
    }


@router.post("/users/{user_id}/suspend")
def suspend_user(user_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_role("admin"))):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_suspended = True
    db.add(user)
    log_event(db, "admin.user.suspend", actor_user_id=principal.user_id, data={"target_user_id": user_id})
    db.commit()
    return {"status": "ok"}


@router.post("/users/{user_id}/unsuspend")
def unsuspend_user(user_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_role("admin"))):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_suspended = False
    db.add(user)
    log_event(db, "admin.user.unsuspend", actor_user_id=principal.user_id, data={"target_user_id": user_id})
    db.commit()
    return {"status": "ok"}


@router.post("/users/{user_id}/revoke-sessions")
def revoke_sessions(
    user_id: str,
    data: RevokeSessionsIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("admin")),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    revoked = 0
    if data.jtis:
        for jti in data.jtis:
            if not jti:
                continue
            db.add(RevokedToken(jti=jti, revoked_at=_now(), reason=data.reason))
            revoked += 1
    log_event(
        db,
        "admin.user.revoke_sessions",
        actor_user_id=principal.user_id,
        data={"target_user_id": user_id, "count": revoked},
    )
    db.commit()
    return {"status": "ok", "revoked": revoked}


@router.post("/users/{user_id}/issue-token")
def issue_token(
    user_id: str,
    data: IssueTokenIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("admin")),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    token = create_user_token(str(user.id), user.role, ttl_minutes=data.ttl_minutes)
    log_event(
        db,
        "admin.user.issue_token",
        actor_user_id=principal.user_id,
        data={"target_user_id": str(user.id), "ttl_minutes": data.ttl_minutes},
    )
    db.commit()
    return {"access_token": token, "token_type": "bearer"}


@router.get("/files")
def admin_files(
    owner_user_id: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(UploadFile)
    if owner_user_id:
        q = q.filter(UploadFile.owner_user_id == owner_user_id)
    if status:
        q = q.filter(UploadFile.status == status)
    rows = q.order_by(UploadFile.created_at.desc()).limit(200).all()
    return {
        "items": [
            {
                "file_id": _public_file_id(r.file_id),
                "original_filename": r.original_filename,
                "status": r.status,
                "visibility": r.visibility,
                "privacy": r.privacy,
                "owner_user_id": str(r.owner_user_id) if r.owner_user_id else None,
                "owner_anon_sub": r.owner_anon_sub or r.owner_sub,
                "created_at": r.created_at,
            }
            for r in rows
        ]
    }


@router.post("/files/{file_id}/hide")
def hide_file(file_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_role("admin"))):
    f = db.query(UploadFile).filter(UploadFile.file_id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    f.visibility = "hidden"
    db.add(f)
    log_event(db, "admin.file.hide", actor_user_id=principal.user_id, file_id=f.file_id)
    db.commit()
    return {"status": "ok"}


@router.post("/files/{file_id}/unhide")
def unhide_file(file_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_role("admin"))):
    f = db.query(UploadFile).filter(UploadFile.file_id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    f.visibility = "private"
    db.add(f)
    log_event(db, "admin.file.unhide", actor_user_id=principal.user_id, file_id=f.file_id)
    db.commit()
    return {"status": "ok"}


@router.post("/files/{file_id}/archive")
def archive_file(file_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_role("admin"))):
    f = db.query(UploadFile).filter(UploadFile.file_id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    f.archived_at = _now()
    db.add(f)
    log_event(db, "admin.file.archive", actor_user_id=principal.user_id, file_id=f.file_id)
    db.commit()
    return {"status": "ok"}


@router.post("/files/{file_id}/unarchive")
def unarchive_file(file_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_role("admin"))):
    f = db.query(UploadFile).filter(UploadFile.file_id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    f.archived_at = None
    db.add(f)
    log_event(db, "admin.file.unarchive", actor_user_id=principal.user_id, file_id=f.file_id)
    db.commit()
    return {"status": "ok"}


@router.delete("/files/{file_id}")
def delete_file(file_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_role("admin"))):
    f = db.query(UploadFile).filter(UploadFile.file_id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    if settings.s3_enabled:
        s3 = get_s3_client(settings)
        for key in [f.object_key, f.gltf_key, f.thumbnail_key]:
            if key:
                try:
                    s3.delete_object(Bucket=f.bucket, Key=key)
                except Exception:
                    pass
    log_event(db, "admin.file.delete", actor_user_id=principal.user_id, file_id=f.file_id)
    db.delete(f)
    db.commit()
    return {"status": "ok"}


@router.get("/shares")
def admin_shares(db: Session = Depends(get_db)):
    rows = db.query(Share).order_by(Share.created_at.desc()).limit(200).all()
    return {
        "items": [
            {
                "id": str(s.id),
                "file_id": _public_file_id(s.file_id),
                "permission": s.permission,
                "expires_at": s.expires_at,
                "revoked_at": s.revoked_at,
                "created_at": s.created_at,
            }
            for s in rows
        ]
    }


@router.get("/approvals")
def admin_approvals(state: Optional[str] = None, limit: int = 200, db: Session = Depends(get_db)):
    limit = max(1, min(limit, 200))
    q = db.query(OrchestratorSession)
    if state:
        q = q.filter(OrchestratorSession.state == str(state).strip().upper())
    else:
        q = q.filter(OrchestratorSession.state == "S5")
    rows = q.order_by(desc(OrchestratorSession.updated_at)).limit(limit).all()
    file_ids = [row.file_id for row in rows]
    file_rows = (
        db.query(UploadFile)
        .filter(UploadFile.file_id.in_(file_ids))
        .all()
        if file_ids
        else []
    )
    by_file_id = {row.file_id: row for row in file_rows}
    return {"items": [_approval_payload(row, by_file_id.get(row.file_id)) for row in rows]}


@router.get("/approvals/{approval_id}")
def admin_approval_detail(approval_id: str, db: Session = Depends(get_db)):
    session = _approval_session_or_404(db, approval_id)
    file_row = db.query(UploadFile).filter(UploadFile.file_id == session.file_id).first()
    return _approval_payload(session, file_row)


@router.post("/approvals/{approval_id}:approve")
def admin_approve_approval(
    approval_id: str,
    data: AdminApprovalIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("admin")),
):
    session = _approval_session_or_404(db, approval_id)
    payload = proxy_orchestra(
        path="/sessions/approve",
        method="POST",
        payload={"session_id": approval_id, "reason": data.reason},
    )
    log_event(
        db,
        "admin.approval.approve",
        actor_user_id=principal.user_id,
        file_id=session.file_id,
        data={"approval_id": approval_id, "reason": data.reason},
    )
    db.commit()
    return payload


@router.post("/approvals/{approval_id}:reject")
def admin_reject_approval(
    approval_id: str,
    data: AdminApprovalIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(require_role("admin")),
):
    session = _approval_session_or_404(db, approval_id)
    payload = proxy_orchestra(
        path="/sessions/reject",
        method="POST",
        payload={"session_id": approval_id, "reason": data.reason},
    )
    log_event(
        db,
        "admin.approval.reject",
        actor_user_id=principal.user_id,
        file_id=session.file_id,
        data={"approval_id": approval_id, "reason": data.reason},
    )
    db.commit()
    return payload


@router.post("/shares/{share_id}/revoke")
def admin_revoke_share(share_id: str, db: Session = Depends(get_db), principal: Principal = Depends(require_role("admin"))):
    share = db.query(Share).filter(Share.id == share_id).first()
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    share.revoked_at = _now()
    db.add(share)
    log_event(
        db,
        "admin.share.revoke",
        actor_user_id=principal.user_id,
        file_id=share.file_id,
        data={"share_id": share_id},
    )
    db.commit()
    return {"status": "ok"}


@router.get("/audit")
def admin_audit(db: Session = Depends(get_db)):
    rows = db.query(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(200).all()
    return {
        "items": [
            {
                "id": str(a.id),
                "action": a.event_type,
                "event_type": a.event_type,
                "actor_user_id": str(a.actor_user_id) if a.actor_user_id else None,
                "actor_anon_sub": a.actor_anon_sub,
                "file_id": _public_file_id(a.file_id),
                "target_type": "file" if a.file_id else "system",
                "target_id": _public_file_id(a.file_id),
                "data": _safe_meta_preview(a.data),
                "meta_preview": _safe_meta_preview(a.data),
                "timestamp": a.created_at,
                "created_at": a.created_at,
            }
            for a in rows
        ]
    }
