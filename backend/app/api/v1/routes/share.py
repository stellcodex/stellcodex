from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.ids import normalize_scx_id
from app.core.config import settings
from app.core.storage import get_s3_client
from app.db.session import get_db
from app.models.file import UploadFile as UploadFileModel
from app.models.share import Share
from app.security.deps import Principal, get_current_principal
from app.services.audit import log_event

router = APIRouter()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _normalize_file_id(value: str) -> str:
    try:
        return normalize_scx_id(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file id")


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
    content_type: str
    original_filename: str
    size_bytes: int
    gltf_url: str | None = None
    original_url: str | None = None
    expires_in_seconds: int = 900


@router.post("/files/{file_id}/share", response_model=ShareCreateOut)
def create_share(
    file_id: str,
    data: ShareCreateIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(get_current_principal),
):
    file_id = _normalize_file_id(file_id)
    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
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
    file_id = _normalize_file_id(file_id)
    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
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


@router.get("/share/{token}", response_model=ShareResolveOut)
def resolve_share(token: str, db: Session = Depends(get_db)):
    share = db.query(Share).filter(Share.token == token).first()
    if not share:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid share token")
    if share.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if _as_utc(share.expires_at) < _now():
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Share expired")

    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == share.file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    if f.status != "ready":
        raise HTTPException(status_code=409, detail="File not ready")

    gltf_url = None
    original_url = None
    if f.gltf_key:
        gltf_url = f"/api/v1/share/{token}/gltf"
    else:
        original_url = f"/api/v1/share/{token}/content"

    return ShareResolveOut(
        file_id=f.file_id,
        status=f.status,
        content_type=f.content_type,
        original_filename=f.original_filename,
        size_bytes=int(f.size_bytes),
        gltf_url=gltf_url,
        original_url=original_url,
        expires_in_seconds=900,
    )


@router.get("/share/{token}/content")
def share_content(token: str, db: Session = Depends(get_db)):
    share = db.query(Share).filter(Share.token == token).first()
    if not share:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid share token")
    if share.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if _as_utc(share.expires_at) < _now():
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Share expired")

    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == share.file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    if f.status != "ready":
        raise HTTPException(status_code=409, detail="File not ready")

    s3 = get_s3_client(settings)
    obj = s3.get_object(Bucket=f.bucket, Key=f.object_key)
    stream = obj["Body"].iter_chunks()
    return StreamingResponse(stream, media_type=f.content_type)


@router.get("/share/{token}/gltf")
def share_gltf(token: str, db: Session = Depends(get_db)):
    share = db.query(Share).filter(Share.token == token).first()
    if not share:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid share token")
    if share.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if _as_utc(share.expires_at) < _now():
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Share expired")

    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == share.file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    if f.status != "ready":
        raise HTTPException(status_code=409, detail="File not ready")
    if not f.gltf_key:
        raise HTTPException(status_code=404, detail="GLTF not found")

    s3 = get_s3_client(settings)
    obj = s3.get_object(Bucket=f.bucket, Key=f.gltf_key)
    stream = obj["Body"].iter_chunks()
    return StreamingResponse(stream, media_type="model/gltf-binary")
