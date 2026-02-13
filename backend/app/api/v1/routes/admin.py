from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from rq.registry import FailedJobRegistry, StartedJobRegistry
from sqlalchemy import desc, text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.storage import get_s3_client
from app.db.session import get_db
from app.models.audit import AuditEvent
from app.models.file import UploadFile
from app.models.job_failure import JobFailure
from app.models.share import Share
from app.models.user import RevokedToken, User
from app.queue import get_queue, redis_conn
from app.security.deps import require_role, Principal
from app.security.jwt import create_user_token
from app.services.audit import log_event

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_role("admin"))])

QUEUE_NAMES = ["cad", "drawing", "render"]


class IssueTokenIn(BaseModel):
    ttl_minutes: int = Field(default=7 * 24 * 60, ge=30, le=30 * 24 * 60)


class RevokeSessionsIn(BaseModel):
    jtis: list[str] | None = None
    reason: str | None = None


def _now() -> datetime:
    return datetime.now(timezone.utc)


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

    payload = {
        "api": "ok",
        "db": "ok" if db_ok else "fail",
        "redis": "ok" if redis_ok else "fail",
        "rq": "ok" if redis_ok else "fail",
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
    return {"queues": queues}


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
                "file_id": r.file_id,
                "stage": r.stage,
                "error_class": r.error_class,
                "message": (r.message or "")[:300],
                "created_at": r.created_at,
            }
            for r in rows
        ]
    }


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
                "file_id": r.file_id,
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
                "file_id": s.file_id,
                "permission": s.permission,
                "expires_at": s.expires_at,
                "revoked_at": s.revoked_at,
                "created_at": s.created_at,
            }
            for s in rows
        ]
    }


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
                "event_type": a.event_type,
                "actor_user_id": str(a.actor_user_id) if a.actor_user_id else None,
                "actor_anon_sub": a.actor_anon_sub,
                "file_id": a.file_id,
                "data": a.data,
                "created_at": a.created_at,
            }
            for a in rows
        ]
    }
