from __future__ import annotations

from datetime import datetime, timezone
import logging
from uuid import uuid4
import tempfile

from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File as FastAPIFile, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.storage import get_s3_client, get_s3_presign_client
from app.db.session import get_db
from app.models.file import UploadFile as UploadFileModel
from app.api.v1.routes.auth import oauth2_scheme, decode_token
from app.services.dxf import load_doc, manifest_from_doc, render_svg

router = APIRouter(tags=["files"])
log = logging.getLogger("uvicorn.error")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _require_user(token: str = Depends(oauth2_scheme)) -> dict:
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid access token")
    return payload


def _feature_on() -> None:
    if not getattr(settings, "feature_files", True):
        raise HTTPException(status_code=404, detail="Feature disabled")


def _allowed_ext(filename: str) -> bool:
    name = (filename or "").lower()
    for ext in [
        ".stl",
        ".step",
        ".stp",
        ".iges",
        ".igs",
        ".brep",
        ".brp",
        ".fcstd",
        ".ifc",
        ".obj",
        ".ply",
        ".off",
        ".3mf",
        ".amf",
        ".dae",
        ".glb",
        ".gltf",
        ".dxf",
        ".pdf",
        ".png",
        ".jpg",
        ".jpeg",
    ]:
        if name.endswith(ext):
            return True
    return False


def _validate_upload(content_type: str, size_bytes: int, filename: str) -> None:
    max_bytes = getattr(settings, "max_upload_bytes", 100 * 1024 * 1024)
    if size_bytes > max_bytes:
        raise HTTPException(status_code=413, detail=f"File too large (max {max_bytes} bytes)")

    allow = getattr(settings, "allowed_content_types", [])
    if allow and (content_type not in allow) and not _allowed_ext(filename):
        raise HTTPException(status_code=415, detail="Unsupported content-type")


def _safe_object_key(owner_sub: str) -> str:
    return f"uploads/{owner_sub}/{uuid4()}/original"


def s3_client():
    try:
        return get_s3_client(settings)
    except RuntimeError:
        raise HTTPException(status_code=500, detail="S3 not configured")


def s3_presign_client():
    try:
        return get_s3_presign_client(settings)
    except RuntimeError:
        raise HTTPException(status_code=500, detail="S3 not configured")


class InitiateIn(BaseModel):
    filename: str
    content_type: str
    size_bytes: int = Field(..., ge=1)
    sha256: str | None = None


class InitiateOut(BaseModel):
    file_id: str
    object_key: str
    upload_url: str
    expires_in_seconds: int = 900


class CompleteIn(BaseModel):
    etag: str | None = None


class FileOut(BaseModel):
    file_id: str
    object_key: str
    original_filename: str
    content_type: str
    size_bytes: int
    status: str
    visibility: str
    job_id: str | None = None
    gltf_key: str | None = None
    thumbnail_key: str | None = None
    preview_url: str | None = None
    error: str | None = None


class FileDetailOut(FileOut):
    gltf_url: str | None = None
    original_url: str | None = None


class PageOut(BaseModel):
    items: list[FileOut]
    page: int
    page_size: int
    total: int


class UrlOut(BaseModel):
    url: str
    expires_in_seconds: int = 900


class VisibilityIn(BaseModel):
    visibility: str = Field(..., pattern="^(private|public|hidden)$")


@router.post("/initiate", response_model=InitiateOut)
def initiate_upload(
    data: InitiateIn,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    _feature_on()
    if not data.filename:
        raise HTTPException(status_code=400, detail="filename required")
    _validate_upload(data.content_type, data.size_bytes, data.filename)

    owner_sub = str(user.get("sub") or "")
    bucket = settings.s3_bucket
    key = _safe_object_key(owner_sub)

    f = UploadFileModel(
        owner_sub=owner_sub,
        bucket=bucket,
        object_key=key,
        original_filename=data.filename,
        content_type=data.content_type,
        size_bytes=data.size_bytes,
        sha256=data.sha256,
        status="pending",
        visibility="private",
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    print(
        f"upload_initiated file_id={f.file_id} object_key={f.object_key} "
        f"size_bytes={int(f.size_bytes)} content_type={f.content_type} "
        f"route=/api/v1/files/initiate"
    )

    s3 = s3_presign_client()
    url = s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket, "Key": key, "ContentType": data.content_type},
        ExpiresIn=900,
    )
    return InitiateOut(file_id=f.file_id, object_key=key, upload_url=url, expires_in_seconds=900)


@router.post("/upload", response_model=FileOut)
async def direct_upload(
    upload: UploadFile = FastAPIFile(...),
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    _feature_on()
    if not upload.filename:
        raise HTTPException(status_code=400, detail="filename required")

    # Determine size without loading whole file into memory
    upload.file.seek(0, 2)
    size_bytes = upload.file.tell()
    upload.file.seek(0)

    content_type = (upload.content_type or "application/octet-stream").strip()
    _validate_upload(content_type, size_bytes, upload.filename)

    owner_sub = str(user.get("sub") or "")
    bucket = settings.s3_bucket
    key = _safe_object_key(owner_sub)

    f = UploadFileModel(
        owner_sub=owner_sub,
        bucket=bucket,
        object_key=key,
        original_filename=upload.filename,
        content_type=content_type,
        size_bytes=size_bytes,
        status="queued",
        visibility="private",
        created_at=_now(),
        updated_at=_now(),
    )
    db.add(f)
    db.commit()
    db.refresh(f)

    s3 = s3_client()
    s3.upload_fileobj(
        upload.file,
        bucket,
        key,
        ExtraArgs={"ContentType": content_type},
    )

    try:
        from app.workers.tasks import enqueue_convert_file
        job_id = enqueue_convert_file(f.file_id)
        if job_id:
            f.meta = {**(f.meta or {}), "job_id": job_id}
            db.add(f)
            db.commit()
        print(
            f"enqueue_success file_id={f.file_id} queue=cad job_id={job_id} "
            f"redis_url={settings.REDIS_URL} route=/api/v1/files/upload"
        )
    except Exception as exc:
        print(
            f"enqueue_failed file_id={f.file_id} queue=cad job_id=None "
            f"redis_url={settings.REDIS_URL} route=/api/v1/files/upload error={exc}"
        )
        job_id = None

    return FileOut(
        file_id=f.file_id,
        object_key=f.object_key,
        original_filename=f.original_filename,
        content_type=f.content_type,
        size_bytes=int(f.size_bytes),
        status=f.status,
        visibility=f.visibility,
        job_id=job_id,
        gltf_key=f.gltf_key,
        thumbnail_key=f.thumbnail_key,
    )


@router.post("/{file_id}/complete", response_model=FileOut)
def complete_upload(
    file_id: str,
    _data: CompleteIn,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    _feature_on()
    owner_sub = str(user.get("sub") or "")

    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    if f.owner_sub != owner_sub:
        raise HTTPException(status_code=403, detail="Forbidden")

    s3 = s3_client()
    try:
        head = s3.head_object(Bucket=f.bucket, Key=f.object_key)
    except ClientError:
        raise HTTPException(status_code=400, detail="Object not uploaded yet")

    remote_size = int(head.get("ContentLength") or 0)
    remote_ct = (head.get("ContentType") or "").strip()

    if remote_size and int(f.size_bytes) and remote_size != int(f.size_bytes):
        raise HTTPException(status_code=400, detail="Uploaded size mismatch")
    if remote_ct and f.content_type and remote_ct != f.content_type:
        raise HTTPException(status_code=400, detail="Uploaded content-type mismatch")

    f.status = "queued"
    f.updated_at = _now()
    db.add(f)
    db.commit()
    db.refresh(f)
    print(
        f"upload_completed file_id={f.file_id} object_key={f.object_key} "
        f"size_bytes={int(f.size_bytes)} content_type={f.content_type} "
        f"route=/api/v1/files/{file_id}/complete"
    )

    try:
        from app.workers.tasks import enqueue_convert_file
        job_id = enqueue_convert_file(f.file_id)
        if job_id:
            f.meta = {**(f.meta or {}), "job_id": job_id}
            db.add(f)
            db.commit()
        print(
            f"enqueue_success file_id={f.file_id} queue=cad job_id={job_id} "
            f"redis_url={settings.REDIS_URL} route=/api/v1/files/{file_id}/complete"
        )
    except Exception as exc:
        print(
            f"enqueue_failed file_id={f.file_id} queue=cad job_id=None "
            f"redis_url={settings.REDIS_URL} route=/api/v1/files/{file_id}/complete error={exc}"
        )
        # If worker queue is down, keep status queued; client can retry later.
        job_id = None

    return FileOut(
        file_id=f.file_id,
        object_key=f.object_key,
        original_filename=f.original_filename,
        content_type=f.content_type,
        size_bytes=int(f.size_bytes),
        status=f.status,
        visibility=f.visibility,
        job_id=job_id,
        gltf_key=f.gltf_key,
        thumbnail_key=f.thumbnail_key,
    )


@router.get("", response_model=PageOut)
def list_files(
    page: int = 1,
    page_size: int = 20,
    include_hidden: bool = False,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    _feature_on()
    if page < 1 or page_size < 1 or page_size > 100:
        raise HTTPException(status_code=400, detail="Invalid pagination")

    owner_sub = str(user.get("sub") or "")
    q = db.query(UploadFileModel).filter(UploadFileModel.owner_sub == owner_sub)
    if not include_hidden:
        q = q.filter(UploadFileModel.visibility != "hidden")
    total = q.count()
    rows = (
        q.order_by(UploadFileModel.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = []
    for r in rows:
        preview_url = None
        if r.status == "ready":
            preview_url = f"/api/v1/files/{r.file_id}/gltf" if r.gltf_key else f"/api/v1/files/{r.file_id}/content"
        err = None
        if r.status == "failed":
            err = (r.meta or {}).get("error")

        items.append(
            FileOut(
                file_id=r.file_id,
                object_key=r.object_key,
                original_filename=r.original_filename,
                content_type=r.content_type,
                size_bytes=int(r.size_bytes),
                status=r.status,
                visibility=r.visibility,
                job_id=None,
                gltf_key=r.gltf_key,
                thumbnail_key=r.thumbnail_key,
                preview_url=preview_url,
                error=err,
            )
        )
    return PageOut(items=items, page=page, page_size=page_size, total=total)


@router.get("/{file_id}", response_model=FileDetailOut)
def get_file(
    file_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    _feature_on()
    owner_sub = str(user.get("sub") or "")
    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    if f.owner_sub != owner_sub:
        raise HTTPException(status_code=403, detail="Forbidden")

    gltf_url = None
    original_url = None
    if f.status == "ready":
        if f.gltf_key:
            gltf_url = f"/api/v1/files/{f.file_id}/gltf"
        else:
            original_url = f"/api/v1/files/{f.file_id}/content"

    return FileDetailOut(
        file_id=f.file_id,
        object_key=f.object_key,
        original_filename=f.original_filename,
        content_type=f.content_type,
        size_bytes=int(f.size_bytes),
        status=f.status,
        visibility=f.visibility,
        job_id=None,
        gltf_key=f.gltf_key,
        thumbnail_key=f.thumbnail_key,
        gltf_url=gltf_url,
        original_url=original_url,
        error=(f.meta or {}).get("error") if f.status == "failed" else None,
    )


@router.post("/{file_id}/download-url", response_model=UrlOut)
def download_url(
    file_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    _feature_on()
    owner_sub = str(user.get("sub") or "")

    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    if f.owner_sub != owner_sub:
        raise HTTPException(status_code=403, detail="Forbidden")
    if f.status != "ready":
        raise HTTPException(status_code=409, detail="File not ready")

    s3 = s3_presign_client()
    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": f.bucket, "Key": f.object_key},
        ExpiresIn=900,
    )
    return UrlOut(url=url, expires_in_seconds=900)


@router.get("/{file_id}/content")
def download_content(
    file_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    _feature_on()
    owner_sub = str(user.get("sub") or "")
    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    if f.owner_sub != owner_sub:
        raise HTTPException(status_code=403, detail="Forbidden")
    if f.status != "ready":
        raise HTTPException(status_code=409, detail="File not ready")

    s3 = s3_client()
    obj = s3.get_object(Bucket=f.bucket, Key=f.object_key)
    stream = obj["Body"].iter_chunks()
    return StreamingResponse(stream, media_type=f.content_type)


@router.get("/{file_id}/gltf")
def download_gltf(
    file_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    _feature_on()
    owner_sub = str(user.get("sub") or "")
    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    if f.owner_sub != owner_sub:
        raise HTTPException(status_code=403, detail="Forbidden")
    if f.status != "ready":
        raise HTTPException(status_code=409, detail="File not ready")
    if not f.gltf_key:
        raise HTTPException(status_code=404, detail="GLTF not found")

    s3 = s3_client()
    obj = s3.get_object(Bucket=f.bucket, Key=f.gltf_key)
    stream = obj["Body"].iter_chunks()
    return StreamingResponse(stream, media_type="model/gltf-binary")


@router.patch("/{file_id}/visibility", response_model=FileOut)
def update_visibility(
    file_id: str,
    data: VisibilityIn,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    _feature_on()
    owner_sub = str(user.get("sub") or "")
    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    if f.owner_sub != owner_sub:
        raise HTTPException(status_code=403, detail="Forbidden")

    f.visibility = data.visibility
    f.updated_at = _now()
    db.add(f)
    db.commit()
    db.refresh(f)

    return FileOut(
        file_id=f.file_id,
        object_key=f.object_key,
        original_filename=f.original_filename,
        content_type=f.content_type,
        size_bytes=int(f.size_bytes),
        status=f.status,
        visibility=f.visibility,
        job_id=None,
        gltf_key=f.gltf_key,
        thumbnail_key=f.thumbnail_key,
    )


def _is_dxf(filename: str) -> bool:
    return (filename or "").lower().endswith(".dxf")


@router.get("/{file_id}/dxf/manifest")
def dxf_manifest(
    file_id: str,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    _feature_on()
    owner_sub = str(user.get("sub") or "")
    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    if f.owner_sub != owner_sub:
        raise HTTPException(status_code=403, detail="Forbidden")
    if f.status != "ready":
        raise HTTPException(status_code=409, detail="File not ready")
    if not _is_dxf(f.original_filename):
        raise HTTPException(status_code=415, detail="Not a DXF file")

    s3 = s3_client()
    obj = s3.get_object(Bucket=f.bucket, Key=f.object_key)
    with tempfile.NamedTemporaryFile(suffix=".dxf") as tmp:
        for chunk in obj["Body"].iter_chunks():
            tmp.write(chunk)
        tmp.flush()
        doc = load_doc(tmp.name)
    return manifest_from_doc(doc)


@router.get("/{file_id}/dxf/render")
def dxf_render(
    file_id: str,
    layers: str | None = None,
    db: Session = Depends(get_db),
    user: dict = Depends(_require_user),
):
    _feature_on()
    owner_sub = str(user.get("sub") or "")
    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    if f.owner_sub != owner_sub:
        raise HTTPException(status_code=403, detail="Forbidden")
    if f.status != "ready":
        raise HTTPException(status_code=409, detail="File not ready")
    if not _is_dxf(f.original_filename):
        raise HTTPException(status_code=415, detail="Not a DXF file")

    visible_layers = None
    if layers is not None:
        visible_layers = {l.strip() for l in layers.split(",") if l.strip()}

    s3 = s3_client()
    obj = s3.get_object(Bucket=f.bucket, Key=f.object_key)
    with tempfile.NamedTemporaryFile(suffix=".dxf") as tmp:
        for chunk in obj["Body"].iter_chunks():
            tmp.write(chunk)
        tmp.flush()
        doc = load_doc(tmp.name)
    svg = render_svg(doc, visible_layers)
    return Response(content=svg, media_type="image/svg+xml")
