from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from jose import jwt, JWTError
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.storage import get_s3_client
from app.db.session import get_db
from app.models.file import UploadFile as UploadFileModel
from app.api.v1.routes.auth import oauth2_scheme, decode_token

router = APIRouter()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _require_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid access token")
    return payload


def _sign_share(file_id: str, expires_in_seconds: int) -> str:
    exp = _now() + timedelta(seconds=expires_in_seconds)
    payload = {"type": "share", "file_id": file_id, "exp": exp}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)


def _verify_share(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALG])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid share token")
    if payload.get("type") != "share":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid share token")
    return payload


class ShareCreateIn(BaseModel):
    file_id: str
    expires_in_seconds: int = Field(default=7 * 24 * 60 * 60, ge=60, le=30 * 24 * 60 * 60)


class ShareCreateOut(BaseModel):
    token: str
    expires_at: datetime


class ShareResolveOut(BaseModel):
    file_id: str
    status: str
    content_type: str
    original_filename: str
    size_bytes: int
    gltf_url: Optional[str] = None
    original_url: Optional[str] = None
    expires_in_seconds: int = 900


@router.post("", response_model=ShareCreateOut)
def create_share(
    data: ShareCreateIn,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    owner_sub = str(user.get("sub") or "")
    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == data.file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    if f.owner_sub != owner_sub:
        raise HTTPException(status_code=403, detail="Forbidden")
    if f.status != "ready":
        raise HTTPException(status_code=409, detail="File not ready")

    token = _sign_share(f.file_id, data.expires_in_seconds)
    return ShareCreateOut(token=token, expires_at=_now() + timedelta(seconds=data.expires_in_seconds))


@router.get("/{token}", response_model=ShareResolveOut)
def resolve_share(token: str, db: Session = Depends(get_db)):
    payload = _verify_share(token)
    file_id = str(payload.get("file_id") or "")
    if not file_id:
        raise HTTPException(status_code=400, detail="Invalid token payload")

    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
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


@router.get("/{token}/content")
def share_content(token: str, db: Session = Depends(get_db)):
    payload = _verify_share(token)
    file_id = str(payload.get("file_id") or "")
    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    if f.status != "ready":
        raise HTTPException(status_code=409, detail="File not ready")

    s3 = get_s3_client(settings)
    obj = s3.get_object(Bucket=f.bucket, Key=f.object_key)
    stream = obj["Body"].iter_chunks()
    return StreamingResponse(stream, media_type=f.content_type)


@router.get("/{token}/gltf")
def share_gltf(token: str, db: Session = Depends(get_db)):
    payload = _verify_share(token)
    file_id = str(payload.get("file_id") or "")
    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
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
