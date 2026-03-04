from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.ids import format_scx_file_id, normalize_scx_file_id, normalize_scx_id
from app.core.config import settings
from app.core.storage import get_s3_client
from app.db.session import get_db
from app.models.file import UploadFile as UploadFileModel
from app.models.share import Share
from app.queue import redis_conn
from app.security.deps import Principal, get_current_principal
from app.services.audit import log_event

router = APIRouter()

SHARE_RATE_LIMIT_WINDOW_SECONDS = 60
SHARE_RATE_LIMIT_REQUESTS = 120
SHARE_RATE_LIMIT_KEY_PREFIX = "stell:share:rate:"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _normalize_file_id(value: str) -> str:
    return format_scx_file_id(_normalize_file_uuid(value))


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


def _token_fingerprint(token: str) -> str:
    if len(token) <= 10:
        return token
    return f"{token[:6]}...{token[-4:]}"


def _client_ip(request: Request | None) -> str:
    if request is None:
        return "unknown"
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if forwarded:
        return forwarded
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _share_event_data(token: str, share: Share, request: Request | None, extra: dict | None = None) -> dict:
    data = {
        "share_id": str(share.id),
        "share_token": _token_fingerprint(token),
        "permission": share.permission,
        "client_ip": _client_ip(request),
        "path": request.url.path if request is not None else None,
        "user_agent": request.headers.get("user-agent") if request is not None else None,
    }
    if extra:
        data.update(extra)
    return data


def _audit_share_event(
    db: Session,
    event_type: str,
    share: Share,
    token: str,
    request: Request | None,
    extra: dict | None = None,
) -> None:
    log_event(
        db,
        event_type,
        file_id=share.file_id,
        data=_share_event_data(token, share, request, extra),
    )
    db.commit()


def _enforce_share_rate_limit(db: Session, share: Share, token: str, request: Request | None) -> None:
    try:
        window_bucket = int(_now().timestamp()) // SHARE_RATE_LIMIT_WINDOW_SECONDS
        rate_key = f"{SHARE_RATE_LIMIT_KEY_PREFIX}{share.id}:{_client_ip(request)}:{window_bucket}"
        request_count = int(redis_conn.incr(rate_key))
        if request_count == 1:
            redis_conn.expire(rate_key, SHARE_RATE_LIMIT_WINDOW_SECONDS + 5)
        if request_count > SHARE_RATE_LIMIT_REQUESTS:
            _audit_share_event(
                db,
                "share.rate_limited",
                share,
                token,
                request,
                extra={
                    "limit": SHARE_RATE_LIMIT_REQUESTS,
                    "window_seconds": SHARE_RATE_LIMIT_WINDOW_SECONDS,
                    "request_count": request_count,
                },
            )
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many share requests")
    except HTTPException:
        raise
    except Exception:
        # Share access should stay available if Redis is temporarily degraded.
        return


class ShareCreateIn(BaseModel):
    permission: str = Field(default="view", pattern="^(view|comment|download)$")
    expires_in_seconds: int = Field(default=7 * 24 * 60 * 60, ge=60, le=30 * 24 * 60 * 60)


class ShareCreateOut(BaseModel):
    id: str
    token: str
    expires_at: datetime
    permission: str


class ShareListOut(BaseModel):
    items: list[ShareCreateOut]


class ShareResolveOut(BaseModel):
    file_id: str
    status: str
    permission: str
    can_view: bool
    can_download: bool
    expires_at: datetime
    content_type: str
    original_filename: str
    size_bytes: int
    gltf_url: str | None = None
    original_url: str | None = None
    expires_in_seconds: int = 900


def _serialize_share_resolve(token: str, share: Share, f: UploadFileModel) -> ShareResolveOut:
    gltf_url = None
    original_url = None
    if f.gltf_key:
        gltf_url = f"/api/v1/share/{token}/gltf"
    else:
        original_url = f"/api/v1/share/{token}/content"

    return ShareResolveOut(
        file_id=_public_file_id(f.file_id),
        status=f.status,
        permission=share.permission,
        can_view=True,
        can_download=share.permission == "download",
        expires_at=share.expires_at,
        content_type=f.content_type,
        original_filename=f.original_filename,
        size_bytes=int(f.size_bytes),
        gltf_url=gltf_url,
        original_url=original_url,
        expires_in_seconds=900,
    )


def _resolve_active_share(
    db: Session,
    token: str,
    request: Request | None = None,
    audit_event: str | None = None,
) -> tuple[Share, UploadFileModel]:
    share = db.query(Share).filter(Share.token == token).first()
    if not share:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid share token")
    if share.revoked_at is not None:
        if request is not None:
            _audit_share_event(db, "share.access_denied", share, token, request, extra={"reason": "revoked"})
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if _as_utc(share.expires_at) < _now():
        if request is not None:
            _audit_share_event(db, "share.access_denied", share, token, request, extra={"reason": "expired"})
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Share expired")

    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == share.file_id).first()
    if not f:
        if request is not None:
            _audit_share_event(db, "share.access_denied", share, token, request, extra={"reason": "file_missing"})
        raise HTTPException(status_code=404, detail="File not found")
    if f.status != "ready":
        if request is not None:
            _audit_share_event(db, "share.access_denied", share, token, request, extra={"reason": "file_not_ready"})
        raise HTTPException(status_code=409, detail="File not ready")

    _enforce_share_rate_limit(db, share, token, request)
    if audit_event and request is not None:
        _audit_share_event(db, audit_event, share, token, request)
    return share, f


@router.post("/files/{file_id}/share", response_model=ShareCreateOut)
def create_share(
    file_id: str,
    data: ShareCreateIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    f = _get_file_by_identifier(db, file_id)
    if not f:
        raise HTTPException(status_code=404, detail="File not found")

    if principal.typ == "guest":
        if f.owner_anon_sub != principal.owner_sub and f.owner_sub != principal.owner_sub:
            raise HTTPException(status_code=403, detail="Forbidden")
    else:
        if str(f.owner_user_id or "") != principal.user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

    if f.status != "ready":
        raise HTTPException(status_code=409, detail="File not ready")

    token = secrets.token_urlsafe(24)
    expires_at = _now() + timedelta(seconds=data.expires_in_seconds)
    share = Share(
        file_id=f.file_id,
        created_by_user_id=principal.user_id,
        token=token,
        permission=data.permission,
        expires_at=expires_at,
    )
    db.add(share)
    log_event(
        db,
        "share.created",
        actor_user_id=principal.user_id,
        actor_anon_sub=principal.owner_sub,
        file_id=f.file_id,
        data={"permission": data.permission, "expires_at": expires_at.isoformat()},
    )
    db.commit()
    db.refresh(share)
    return ShareCreateOut(id=str(share.id), token=share.token, expires_at=share.expires_at, permission=share.permission)


@router.get("/files/{file_id}/shares", response_model=ShareListOut)
def list_shares(
    file_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    f = _get_file_by_identifier(db, file_id)
    if not f:
        raise HTTPException(status_code=404, detail="File not found")

    if principal.typ == "guest":
        if f.owner_anon_sub != principal.owner_sub and f.owner_sub != principal.owner_sub:
            raise HTTPException(status_code=403, detail="Forbidden")
    else:
        if str(f.owner_user_id or "") != principal.user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

    rows = (
        db.query(Share)
        .filter(Share.file_id == f.file_id)
        .order_by(Share.created_at.desc())
        .all()
    )
    items = [
        ShareCreateOut(id=str(s.id), token=s.token, expires_at=s.expires_at, permission=s.permission)
        for s in rows
    ]
    return ShareListOut(items=items)


@router.post("/shares/{share_id}/revoke")
def revoke_share(
    share_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    share = db.query(Share).filter(Share.id == share_id).first()
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")

    if principal.typ == "user":
        if share.created_by_user_id and str(share.created_by_user_id) != principal.user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
    else:
        # guests can only revoke if they own the file
        f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == share.file_id).first()
        if not f or (f.owner_anon_sub != principal.owner_sub and f.owner_sub != principal.owner_sub):
            raise HTTPException(status_code=403, detail="Forbidden")

    share.revoked_at = _now()
    log_event(
        db,
        "share.revoked",
        actor_user_id=principal.user_id,
        actor_anon_sub=principal.owner_sub,
        file_id=share.file_id,
        data={"share_id": str(share.id)},
    )
    db.add(share)
    db.commit()
    return {"status": "ok"}


@router.get("/share/resolve", response_model=ShareResolveOut)
def resolve_share_query(
    share_token: str | None = None,
    token: str | None = None,
    request: Request = None,
    db: Session = Depends(get_db),
):
    effective_token = (share_token or token or "").strip()
    if not effective_token:
        raise HTTPException(status_code=400, detail="share_token or token query parameter required")
    share, f = _resolve_active_share(db, effective_token, request=request, audit_event="share.resolved")
    return _serialize_share_resolve(effective_token, share, f)


@router.get("/share/{token}", response_model=ShareResolveOut)
def resolve_share(token: str, request: Request, db: Session = Depends(get_db)):
    share, f = _resolve_active_share(db, token, request=request, audit_event="share.resolved")
    return _serialize_share_resolve(token, share, f)


@router.get("/shares/{token}", response_model=ShareResolveOut)
def resolve_share_alias(token: str, request: Request, db: Session = Depends(get_db)):
    share, f = _resolve_active_share(db, token, request=request, audit_event="share.resolved")
    return _serialize_share_resolve(token, share, f)


@router.get("/s/{token}", response_model=ShareResolveOut)
def resolve_share_short_alias(token: str, request: Request, db: Session = Depends(get_db)):
    share, f = _resolve_active_share(db, token, request=request, audit_event="share.resolved")
    return _serialize_share_resolve(token, share, f)


@router.get("/share/{token}/content")
def share_content(token: str, request: Request, db: Session = Depends(get_db)):
    _share, f = _resolve_active_share(db, token, request=request, audit_event="share.content_accessed")

    s3 = get_s3_client(settings)
    obj = s3.get_object(Bucket=f.bucket, Key=f.object_key)
    stream = obj["Body"].iter_chunks()
    return StreamingResponse(stream, media_type=f.content_type)


@router.get("/share/{token}/gltf")
def share_gltf(token: str, request: Request, db: Session = Depends(get_db)):
    _share, f = _resolve_active_share(db, token, request=request, audit_event="share.gltf_accessed")
    if not f.gltf_key:
        raise HTTPException(status_code=404, detail="GLTF not found")

    s3 = get_s3_client(settings)
    obj = s3.get_object(Bucket=f.bucket, Key=f.gltf_key)
    stream = obj["Body"].iter_chunks()
    return StreamingResponse(stream, media_type="model/gltf-binary")
