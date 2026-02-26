from __future__ import annotations

from datetime import datetime, timezone
import io
import json
import logging
import tempfile
import zipfile
from typing import Any
from uuid import uuid4

from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File as FastAPIFile, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.formats import is_allowed_filename, rejected_extensions
from app.core.ids import normalize_scx_id
from app.core.storage import get_s3_client, get_s3_presign_client
from app.db.session import get_db
from app.models.file import UploadFile as UploadFileModel
from app.security.deps import get_current_principal, Principal
from app.services.dxf import load_doc, manifest_from_doc, render_svg
from app.services.audit import log_event

router = APIRouter(tags=["files"])
log = logging.getLogger("uvicorn.error")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _require_principal(principal: Principal = Depends(get_current_principal)) -> Principal:
    return principal


def _feature_on() -> None:
    if not getattr(settings, "feature_files", True):
        raise HTTPException(status_code=404, detail="Feature disabled")


def _allowed_ext(filename: str) -> bool:
    return is_allowed_filename(filename)


def _validate_upload(content_type: str, size_bytes: int, filename: str) -> None:
    max_bytes = getattr(settings, "max_upload_bytes", 100 * 1024 * 1024)
    if size_bytes > max_bytes:
        raise HTTPException(status_code=413, detail=f"File too large (max {max_bytes} bytes)")

    allow = getattr(settings, "allowed_content_types", [])
    if allow and (content_type not in allow) and not _allowed_ext(filename):
        raise HTTPException(status_code=415, detail="Unsupported content-type")
    if not _allowed_ext(filename):
        ext = (filename or "").lower().rsplit(".", 1)[-1]
        if ext in rejected_extensions():
            raise HTTPException(status_code=415, detail="Unsupported file type")
        raise HTTPException(status_code=415, detail="Unsupported file type")


def _normalize_file_id(value: str) -> str:
    try:
        return normalize_scx_id(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file id")


def _safe_object_key(owner_sub: str) -> str:
    return f"uploads/{owner_sub}/{uuid4()}/original"


def _assert_file_access(f: UploadFileModel, principal: Principal) -> None:
    if principal.typ == "guest":
        owner_sub = principal.owner_sub or ""
        if f.owner_anon_sub != owner_sub and f.owner_sub != owner_sub:
            raise HTTPException(status_code=403, detail="Forbidden")
        return

    if str(f.owner_user_id or "") != str(principal.user_id or ""):
        raise HTTPException(status_code=403, detail="Forbidden")


def _is_numeric_scalar(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_placeholder_map(data: dict[str, Any]) -> bool:
    if bool(data.get("placeholder")) or bool(data.get("is_placeholder")):
        return True
    status = data.get("status")
    if isinstance(status, str) and status.strip().lower() == "placeholder":
        return True
    kind = data.get("kind")
    if isinstance(kind, str) and kind.strip().lower() == "placeholder":
        return True
    return False


def _bbox_has_numeric_bounds(bbox: dict[str, Any]) -> bool:
    keys_3d = ("min_x", "min_y", "min_z", "max_x", "max_y", "max_z")
    if all(_is_numeric_scalar(bbox.get(key)) for key in keys_3d):
        return True

    keys_2d = ("min_x", "min_y", "max_x", "max_y")
    if all(_is_numeric_scalar(bbox.get(key)) for key in keys_2d):
        return True

    min_vec = bbox.get("min")
    max_vec = bbox.get("max")
    if (
        isinstance(min_vec, (list, tuple))
        and isinstance(max_vec, (list, tuple))
        and len(min_vec) == len(max_vec)
        and len(min_vec) in {2, 3}
        and all(_is_numeric_scalar(v) for v in min_vec)
        and all(_is_numeric_scalar(v) for v in max_vec)
    ):
        return True

    return False


def _clean_bbox(bbox: dict[str, Any]) -> dict[str, Any]:
    if _is_placeholder_map(bbox):
        return {}
    cleaned = {k: v for k, v in bbox.items() if k not in {"placeholder", "is_placeholder"}}
    if not _bbox_has_numeric_bounds(cleaned):
        return {}
    return cleaned


def _clean_lod_stats(lod_stats: dict[str, Any]) -> dict[str, Any]:
    if _is_placeholder_map(lod_stats):
        return {}
    cleaned: dict[str, Any] = {}
    for key, value in lod_stats.items():
        if key in {"placeholder", "is_placeholder"}:
            continue
        if isinstance(value, dict):
            if _is_placeholder_map(value):
                continue
            nested = {k: v for k, v in value.items() if k not in {"placeholder", "is_placeholder"}}
            if nested:
                cleaned[key] = nested
            continue
        cleaned[key] = value
    return cleaned


def _coerce_bbox(meta: dict[str, Any]) -> dict[str, Any]:
    bbox = meta.get("bbox")
    if isinstance(bbox, dict):
        cleaned_bbox = _clean_bbox(bbox)
        if cleaned_bbox:
            return cleaned_bbox

    nested = meta.get("metadata")
    if isinstance(nested, dict):
        nested_bbox = nested.get("bbox")
        if isinstance(nested_bbox, dict):
            cleaned_nested_bbox = _clean_bbox(nested_bbox)
            if cleaned_nested_bbox:
                return cleaned_nested_bbox

    return {}


def _coerce_lod_stats(meta: dict[str, Any]) -> dict[str, Any]:
    lod_stats = meta.get("lod_stats")
    if isinstance(lod_stats, dict):
        cleaned_lod_stats = _clean_lod_stats(lod_stats)
        if cleaned_lod_stats:
            return cleaned_lod_stats

    nested = meta.get("metadata")
    if not isinstance(nested, dict):
        return {}

    lod0: dict[str, Any] = {}
    faces = nested.get("faces")
    if isinstance(faces, int):
        lod0["triangle_count"] = faces
    vertices = nested.get("vertices")
    if isinstance(vertices, int):
        lod0["vertex_count"] = vertices
    meshes = nested.get("meshes")
    if isinstance(meshes, int):
        lod0["mesh_count_assimp"] = meshes

    return {"lod0": lod0} if lod0 else {}


def _count_parts_in_tree(nodes: Any) -> int:
    if not isinstance(nodes, list):
        return 0

    def _walk(items: list[Any]) -> int:
        total = 0
        for item in items:
            if not isinstance(item, dict):
                continue
            children = item.get("children")
            explicit = item.get("part_count")
            kind = str(item.get("kind") or "").lower()
            has_children = isinstance(children, list) and len(children) > 0
            if isinstance(explicit, int) and explicit >= 0 and not has_children:
                total += explicit
            elif kind == "part":
                total += 1
            if isinstance(children, list):
                total += _walk(children)
        return total

    return _walk(nodes)


def _triangles_from_meta(f: UploadFileModel, lod_name: str) -> int | None:
    meta = f.meta or {}
    stats = meta.get("lod_stats")
    if isinstance(stats, dict):
        value = stats.get(lod_name)
        if isinstance(value, dict):
            tri = value.get("triangle_count")
            if isinstance(tri, int):
                return tri
    return None


def _build_lod_map(f: UploadFileModel) -> dict[str, dict[str, Any]]:
    meta = f.meta or {}
    lod_meta = meta.get("lods")
    lods: dict[str, dict[str, Any]] = {}

    if isinstance(lod_meta, dict):
        for lod_name in ("lod0", "lod1", "lod2"):
            raw = lod_meta.get(lod_name)
            if not isinstance(raw, dict):
                continue
            key = raw.get("key")
            if not isinstance(key, str) or not key:
                continue
            lods[lod_name] = {
                "key": key,
                "ready": bool(raw.get("ready", False)),
                "url": f"/api/v1/files/{f.file_id}/lod/{lod_name}",
                "triangle_count": _triangles_from_meta(f, lod_name),
            }

    if "lod0" not in lods and f.gltf_key:
        lods["lod0"] = {
            "key": f.gltf_key,
            "ready": f.status == "ready",
            "url": f"/api/v1/files/{f.file_id}/gltf",
            "triangle_count": _triangles_from_meta(f, "lod0"),
        }

    return lods


def _build_scx_manifest(f: UploadFileModel, lods: dict[str, dict[str, Any]]) -> dict[str, Any]:
    meta = f.meta or {}
    defaults = meta.get("defaults") if isinstance(meta.get("defaults"), dict) else {}
    assembly_tree = meta.get("assembly_tree") if isinstance(meta.get("assembly_tree"), list) else []
    bbox = _coerce_bbox(meta)
    lod_stats = _coerce_lod_stats(meta)
    part_count = _count_parts_in_tree(assembly_tree)
    if part_count:
        lod0_stats = lod_stats.get("lod0") if isinstance(lod_stats.get("lod0"), dict) else {}
        lod_stats = {
            **lod_stats,
            "lod0": {**lod0_stats, "part_count": int(lod0_stats.get("part_count") or part_count)},
        }

    lod_paths: dict[str, str] = {}
    for lod_name in ("lod0", "lod1", "lod2"):
        if lod_name in lods:
            lod_paths[lod_name] = f"assets/lod/{lod_name}.glb"

    return {
        "format_version": "1.0.0",
        "app": "STELLCODEX",
        "model_id": f.file_id,
        "units": "mm",
        "bbox": bbox,
        "lod": lod_paths,
        "thumbnails": {
            "preview": "assets/thumbs/preview.png" if f.thumbnail_key else None,
            "shaded": "assets/thumbs/shaded.png" if f.thumbnail_key else None,
            "shaded_edge": "assets/thumbs/shaded_edge.png" if f.thumbnail_key else None,
            "hiddenline": "assets/thumbs/hiddenline.png" if f.thumbnail_key else None,
        },
        "defaults": {
            "view_mode": defaults.get("view_mode", "shaded_edge"),
            "quality": defaults.get("quality", "Ultra"),
            "camera": defaults.get("camera", "iso_default"),
        },
        "assembly_tree": assembly_tree,
        "stats": lod_stats,
        "part_count": part_count or None,
    }


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
    lods: dict[str, dict[str, Any]] | None = None
    quality_default: str = "Ultra"
    view_mode_default: str = "shaded_edge"


class PageOut(BaseModel):
    items: list[FileOut]
    page: int
    page_size: int
    total: int


class UrlOut(BaseModel):
    url: str
    expires_in_seconds: int = 900


class StatusOut(BaseModel):
    state: str
    derivatives_available: list[str]
    progress_hint: str | None = None


class RenderIn(BaseModel):
    preset: str


class RenderOut(BaseModel):
    job_id: str
    preset: str


class VisibilityIn(BaseModel):
    visibility: str = Field(..., pattern="^(private|public|hidden)$")


@router.post("/initiate", response_model=InitiateOut)
def initiate_upload(
    data: InitiateIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    if not data.filename:
        raise HTTPException(status_code=400, detail="filename required")
    _validate_upload(data.content_type, data.size_bytes, data.filename)

    owner_sub = principal.owner_sub or principal.user_id or ""
    if not owner_sub:
        raise HTTPException(status_code=401, detail="Unauthorized")
    bucket = settings.s3_bucket
    key = _safe_object_key(owner_sub)

    f = UploadFileModel(
        owner_sub=owner_sub,
        owner_user_id=principal.user_id if principal.typ == "user" else None,
        owner_anon_sub=principal.owner_sub if principal.typ == "guest" else None,
        is_anonymous=principal.typ == "guest",
        privacy="private",
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
    principal: Principal = Depends(_require_principal),
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

    owner_sub = principal.owner_sub or principal.user_id or ""
    if not owner_sub:
        raise HTTPException(status_code=401, detail="Unauthorized")
    bucket = settings.s3_bucket
    key = _safe_object_key(owner_sub)

    f = UploadFileModel(
        owner_sub=owner_sub,
        owner_user_id=principal.user_id if principal.typ == "user" else None,
        owner_anon_sub=principal.owner_sub if principal.typ == "guest" else None,
        is_anonymous=principal.typ == "guest",
        privacy="private",
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

    log_event(
        db,
        "upload.created",
        actor_user_id=principal.user_id,
        actor_anon_sub=principal.owner_sub,
        file_id=f.file_id,
        data={"filename": f.original_filename, "size_bytes": int(f.size_bytes)},
    )
    db.commit()

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
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    owner_sub = principal.owner_sub or principal.user_id or ""
    if not owner_sub:
        raise HTTPException(status_code=401, detail="Unauthorized")

    file_id = _normalize_file_id(file_id)
    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(f, principal)

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
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    if page < 1 or page_size < 1 or page_size > 100:
        raise HTTPException(status_code=400, detail="Invalid pagination")

    owner_sub = principal.owner_sub or ""
    if principal.typ == "guest":
        q = db.query(UploadFileModel).filter(
            (UploadFileModel.owner_anon_sub == owner_sub) | (UploadFileModel.owner_sub == owner_sub)
        )
    else:
        q = db.query(UploadFileModel).filter(UploadFileModel.owner_user_id == principal.user_id)
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
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    owner_sub = principal.owner_sub or ""
    file_id = _normalize_file_id(file_id)
    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(f, principal)

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
        lods=_build_lod_map(f),
        error=(f.meta or {}).get("error") if f.status == "failed" else None,
    )


@router.get("/{file_id}/manifest")
def file_manifest(
    file_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    owner_sub = principal.owner_sub or ""
    file_id = _normalize_file_id(file_id)
    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(f, principal)
    lods = _build_lod_map(f)
    return _build_scx_manifest(f, lods)


@router.get("/{file_id}/scx")
def download_scx(
    file_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    owner_sub = principal.owner_sub or ""
    file_id = _normalize_file_id(file_id)
    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(f, principal)
    if f.status != "ready":
        raise HTTPException(status_code=409, detail="File not ready")

    lods = _build_lod_map(f)
    manifest = _build_scx_manifest(f, lods)
    s3 = s3_client()
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("scx/manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        zf.writestr("scx/materials/material_profile.json", "{}\n")
        zf.writestr("scx/view/camera_presets.json", "[]\n")
        zf.writestr("scx/view/render_presets.json", "[]\n")
        zf.writestr("scx/annotations/measurements.json", "[]\n")
        zf.writestr("scx/annotations/notes.json", "[]\n")
        zf.writestr("scx/security/hashes.json", "{}\n")

        for lod_name, lod in lods.items():
            key = lod.get("key")
            if not isinstance(key, str) or not key:
                continue
            try:
                obj = s3.get_object(Bucket=f.bucket, Key=key)
                zf.writestr(f"scx/assets/lod/{lod_name}.glb", obj["Body"].read())
            except Exception:
                continue

        if f.thumbnail_key:
            try:
                thumb = s3.get_object(Bucket=f.bucket, Key=f.thumbnail_key)["Body"].read()
                zf.writestr("scx/assets/thumbs/preview.png", thumb)
                zf.writestr("scx/assets/thumbs/shaded.png", thumb)
                zf.writestr("scx/assets/thumbs/shaded_edge.png", thumb)
                zf.writestr("scx/assets/thumbs/hiddenline.png", thumb)
            except Exception:
                pass

    zip_buffer.seek(0)
    headers = {"Content-Disposition": f'attachment; filename="{f.file_id}.scx"'}
    return StreamingResponse(zip_buffer, media_type="application/zip", headers=headers)


@router.get("/{file_id}/status", response_model=StatusOut)
def file_status(
    file_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    owner_sub = principal.owner_sub or ""
    file_id = _normalize_file_id(file_id)
    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(f, principal)

    status = (f.status or "").lower()
    if status in {"pending", "queued"}:
        state = "queued"
    elif status in {"processing", "running"}:
        state = "running"
    elif status in {"ready", "succeeded"}:
        state = "succeeded"
    elif status == "failed":
        state = "failed"
    else:
        state = "queued"

    derivatives: list[str] = []
    if f.gltf_key:
        derivatives.append("gltf")
    if f.thumbnail_key:
        derivatives.append("thumbnail")
    if f.content_type.startswith("image/") or f.content_type == "application/pdf":
        if f.status == "ready":
            derivatives.append("original")
    if (f.original_filename or "").lower().endswith(".dxf"):
        if f.status == "ready":
            derivatives.append("dxf")

    progress_hint = None
    if f.meta and isinstance(f.meta, dict):
        progress_hint = f.meta.get("progress")
    if not progress_hint:
        progress_hint = f.status

    return StatusOut(state=state, derivatives_available=derivatives, progress_hint=progress_hint)


@router.post("/{file_id}/render", response_model=RenderOut)
def enqueue_render(
    file_id: str,
    data: RenderIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    owner_sub = principal.owner_sub or ""
    file_id = _normalize_file_id(file_id)
    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(f, principal)
    if f.status != "ready":
        raise HTTPException(status_code=409, detail="File not ready")

    from app.workers.tasks import enqueue_render_preset

    job_id = enqueue_render_preset(f.file_id, data.preset)
    f.meta = {**(f.meta or {}), "render_job_id": job_id}
    db.add(f)
    db.commit()
    return RenderOut(job_id=job_id, preset=data.preset)


@router.post("/{file_id}/download-url", response_model=UrlOut)
def download_url(
    file_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    owner_sub = principal.owner_sub or ""

    file_id = _normalize_file_id(file_id)
    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(f, principal)
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
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    owner_sub = principal.owner_sub or ""
    file_id = _normalize_file_id(file_id)
    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(f, principal)
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
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    owner_sub = principal.owner_sub or ""
    file_id = _normalize_file_id(file_id)
    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(f, principal)
    if f.status != "ready":
        raise HTTPException(status_code=409, detail="File not ready")
    if not f.gltf_key:
        raise HTTPException(status_code=404, detail="GLTF not found")

    s3 = s3_client()
    obj = s3.get_object(Bucket=f.bucket, Key=f.gltf_key)
    stream = obj["Body"].iter_chunks()
    return StreamingResponse(stream, media_type="model/gltf-binary")


@router.get("/{file_id}/lod/{lod_name}")
def download_lod(
    file_id: str,
    lod_name: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    owner_sub = principal.owner_sub or ""
    file_id = _normalize_file_id(file_id)
    if lod_name not in {"lod0", "lod1", "lod2"}:
        raise HTTPException(status_code=400, detail="Invalid LOD")
    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(f, principal)
    if f.status != "ready":
        raise HTTPException(status_code=409, detail="File not ready")

    lods = _build_lod_map(f)
    lod = lods.get(lod_name)
    if not lod:
        raise HTTPException(status_code=404, detail="LOD not found")
    key = lod.get("key")
    if not isinstance(key, str) or not key:
        raise HTTPException(status_code=404, detail="LOD key not found")

    s3 = s3_client()
    obj = s3.get_object(Bucket=f.bucket, Key=key)
    stream = obj["Body"].iter_chunks()
    return StreamingResponse(stream, media_type="model/gltf-binary")


@router.patch("/{file_id}/visibility", response_model=FileOut)
def update_visibility(
    file_id: str,
    data: VisibilityIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    owner_sub = principal.owner_sub or ""
    file_id = _normalize_file_id(file_id)
    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(f, principal)

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
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    owner_sub = principal.owner_sub or ""
    file_id = _normalize_file_id(file_id)
    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(f, principal)
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
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    owner_sub = principal.owner_sub or ""
    file_id = _normalize_file_id(file_id)
    f: UploadFileModel | None = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(f, principal)
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
