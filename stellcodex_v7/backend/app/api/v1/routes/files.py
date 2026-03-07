from __future__ import annotations

from datetime import datetime, timezone
import io
import json
import logging
import os
import tempfile
import zipfile
from typing import Any, Union
from uuid import UUID, uuid4

from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException, Depends, Form, UploadFile, File as FastAPIFile, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.format_registry import (
    allowed_extensions as registry_allowed_extensions,
    extension_from_filename,
    get_rule_for_filename,
    grouped_payload,
    infer_mime_from_bytes,
    match_content_type,
    rejected_extensions as registry_rejected_extensions,
)
from app.core.ids import format_scx_file_id, normalize_scx_file_id, normalize_scx_id
from app.core.storage import get_s3_client, get_s3_presign_client
from app.db.session import get_db
from app.models.file import UploadFile as UploadFileModel
from app.security.deps import get_current_principal, Principal
from app.services.dxf import load_doc, manifest_from_doc, render_svg
from app.services.audit import log_event
from app.services.orchestrator_engine import (
    build_decision_json,
    load_rule_config_map,
    upsert_orchestrator_session,
)

router = APIRouter(tags=["files"])
log = logging.getLogger("uvicorn.error")

UPLOAD_RATE_LIMIT_PER_HOUR = int(os.getenv("UPLOAD_RATE_LIMIT_PER_HOUR", "120"))
_UPLOAD_RATE_BUCKET: dict[str, tuple[int, int]] = {}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _require_principal(principal: Principal = Depends(get_current_principal)) -> Principal:
    return principal


def _feature_on() -> None:
    if not getattr(settings, "feature_files", True):
        raise HTTPException(status_code=404, detail="Feature disabled")


def _allowed_ext(filename: str) -> bool:
    rule = get_rule_for_filename(filename)
    return bool(rule and rule.accept)

def _upload_rate_key(principal: Principal) -> str:
    if principal.typ == "guest":
        return f"guest:{principal.owner_sub or 'anon'}"
    return f"user:{principal.user_id or principal.owner_sub or 'unknown'}"


def _check_upload_rate(principal: Principal) -> None:
    now = int(datetime.now(timezone.utc).timestamp())
    slot = now // 3600
    key = _upload_rate_key(principal)
    seen_slot, count = _UPLOAD_RATE_BUCKET.get(key, (slot, 0))
    if seen_slot != slot:
        seen_slot = slot
        count = 0
    count += 1
    _UPLOAD_RATE_BUCKET[key] = (seen_slot, count)
    if count > UPLOAD_RATE_LIMIT_PER_HOUR:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")


def _validate_upload(content_type: str, size_bytes: int, filename: str, sniffed_content_type: str | None = None) -> None:
    max_bytes = getattr(settings, "max_upload_bytes", 100 * 1024 * 1024)
    if size_bytes > max_bytes:
        raise HTTPException(status_code=413, detail=f"File too large (max {max_bytes} bytes)")

    ext = extension_from_filename(filename)
    rule = get_rule_for_filename(filename)
    if not rule:
        supported = ", ".join(registry_allowed_extensions())
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '.{ext}'. STEP export required for unsupported CAD. Supported: {supported}",
        )
    if not rule.accept:
        supported = ", ".join(registry_allowed_extensions())
        reason = rule.reject_reason or "Unsupported file type"
        raise HTTPException(status_code=415, detail=f"{reason}. Supported: {supported}")

    allow = getattr(settings, "allowed_content_types", [])
    if allow and content_type and (content_type not in allow) and not rule.accept:
        raise HTTPException(status_code=415, detail="Unsupported content-type")

    if content_type and not match_content_type(content_type, ext):
        raise HTTPException(status_code=415, detail=f"Content-Type mismatch for .{ext}")

    if sniffed_content_type:
        if not match_content_type(sniffed_content_type, ext):
            raise HTTPException(status_code=415, detail=f"MIME sniff mismatch for .{ext}")


def _normalize_file_uuid(value: str) -> UUID:
    try:
        return normalize_scx_file_id(value)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid file id")


def _normalize_file_id(value: str) -> str:
    return format_scx_file_id(_normalize_file_uuid(value))


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


def _safe_object_key(owner_sub: str) -> str:
    return f"uploads/{owner_sub}/{uuid4()}/original"


def _derive_kind_mode(filename: str, meta: dict[str, Any] | None = None) -> tuple[str, str]:
    payload = meta if isinstance(meta, dict) else {}
    rule = get_rule_for_filename(filename)
    kind = str(payload.get("kind") or (rule.kind if rule else "3d"))
    mode = str(payload.get("mode") or (rule.mode if rule else "brep"))
    return kind, mode


def _derive_folder_key(filename: str, meta: dict[str, Any] | None = None) -> str:
    payload = meta if isinstance(meta, dict) else {}
    project_id = str(payload.get("project_id") or "default")
    kind, mode = _derive_kind_mode(filename, payload)
    return f"project/{project_id}/{kind}/{mode}"


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


def _build_lod_map(f: UploadFileModel, include_key: bool = False) -> dict[str, dict[str, Any]]:
    meta = f.meta or {}
    lod_meta = meta.get("lods")
    lods: dict[str, dict[str, Any]] = {}
    public_file_id = _public_file_id(f.file_id)

    if isinstance(lod_meta, dict):
        for lod_name in ("lod0", "lod1", "lod2"):
            raw = lod_meta.get(lod_name)
            if not isinstance(raw, dict):
                continue
            key = raw.get("key")
            if not isinstance(key, str) or not key:
                continue
            lod_entry: dict[str, Any] = {
                "ready": bool(raw.get("ready", False)),
                "url": f"/api/v1/files/{public_file_id}/lod/{lod_name}",
                "triangle_count": _triangles_from_meta(f, lod_name),
            }
            if include_key:
                lod_entry["key"] = key
            lods[lod_name] = lod_entry

    if "lod0" not in lods and f.gltf_key:
        lod0_entry: dict[str, Any] = {
            "ready": f.status == "ready",
            "url": f"/api/v1/files/{public_file_id}/gltf",
            "triangle_count": _triangles_from_meta(f, "lod0"),
        }
        if include_key:
            lod0_entry["key"] = f.gltf_key
        lods["lod0"] = lod0_entry

    return lods


def _assembly_tree_from_assembly_meta(payload: dict[str, Any]) -> list[dict[str, Any]]:
    occurrences = payload.get("occurrences")
    if not isinstance(occurrences, list):
        return []
    occurrence_to_nodes = (
        payload.get("occurrence_id_to_gltf_nodes")
        if isinstance(payload.get("occurrence_id_to_gltf_nodes"), dict)
        else {}
    )

    tree: list[dict[str, Any]] = []
    for idx, item in enumerate(occurrences):
        if not isinstance(item, dict):
            continue
        occurrence_id = str(item.get("occurrence_id") or f"occ_{idx + 1:03d}")
        part_id = str(item.get("part_id") or occurrence_id)
        label = str(item.get("name") or item.get("display_name") or part_id)
        mapped_nodes = occurrence_to_nodes.get(occurrence_id, [])
        gltf_nodes = [node for node in mapped_nodes if isinstance(node, str) and node.strip()]
        tree.append(
            {
                "id": occurrence_id,
                "occurrence_id": occurrence_id,
                "part_id": part_id,
                "name": label,
                "display_name": label,
                "kind": "part",
                "part_count": 1,
                "gltf_nodes": gltf_nodes,
                "children": [],
            }
        )
    return tree


def _resolve_assembly_tree(f: UploadFileModel, meta: dict[str, Any]) -> list[dict[str, Any]]:
    existing_tree = meta.get("assembly_tree")
    if isinstance(existing_tree, list) and existing_tree:
        return existing_tree

    assembly_key = meta.get("assembly_meta_key")
    if not isinstance(assembly_key, str) or not assembly_key:
        return []

    try:
        s3 = s3_client()
        obj = s3.get_object(Bucket=f.bucket, Key=assembly_key)
        raw = obj["Body"].read()
        payload = json.loads(raw.decode("utf-8"))
    except Exception:
        return []
    if not isinstance(payload, dict):
        return []
    return _assembly_tree_from_assembly_meta(payload)


def _build_scx_manifest(f: UploadFileModel, lods: dict[str, dict[str, Any]]) -> dict[str, Any]:
    meta = f.meta or {}
    defaults = meta.get("defaults") if isinstance(meta.get("defaults"), dict) else {}
    assembly_tree = _resolve_assembly_tree(f, meta)
    bbox = _coerce_bbox(meta)
    lod_stats = _coerce_lod_stats(meta)
    part_count = _count_parts_in_tree(assembly_tree)
    if part_count <= 0:
        explicit = meta.get("part_count")
        if isinstance(explicit, int) and explicit > 0:
            part_count = explicit
        else:
            geometry = _geometry_meta(f) or {}
            geometry_count = geometry.get("part_count")
            if isinstance(geometry_count, int) and geometry_count > 0:
                part_count = geometry_count
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
        "model_id": _public_file_id(f.file_id),
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
            "quality": defaults.get("quality", "Medium"),
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
    upload_url: str
    expires_in_seconds: int = 900


class CompleteIn(BaseModel):
    etag: str | None = None


class FileOut(BaseModel):
    file_id: str
    original_name: str
    kind: str
    mode: str | None = None
    created_at: datetime
    content_type: str
    size_bytes: int
    status: str
    visibility: str
    thumbnail_url: str | None = None
    preview_url: str | None = None
    preview_urls: list[str] | None = None
    gltf_url: str | None = None
    original_url: str | None = None
    bbox_meta: dict[str, Any] | None = None
    part_count: int | None = None
    error: str | None = None


class FileDetailOut(FileOut):
    lods: dict[str, dict[str, Any]] | None = None
    quality_default: str = "Medium"
    view_mode_default: str = "shaded_edge"


class FileVersionOut(BaseModel):
    version_no: int
    created_at: datetime
    status: str


class FileVersionsOut(BaseModel):
    file_id: str
    versions: list[FileVersionOut]


class PageOut(BaseModel):
    items: list[FileOut]
    page: int
    page_size: int
    total: int


class RecentFileOut(BaseModel):
    file_id: str
    original_name: str
    kind: str
    status: str
    created_at: datetime
    thumbnail_url: str | None = None


class RecentPageOut(BaseModel):
    items: list[RecentFileOut]
    limit: int


class UrlOut(BaseModel):
    url: str
    expires_in_seconds: int = 900


class StatusOut(BaseModel):
    state: str
    derivatives_available: list[str]
    progress_hint: str | None = None
    progress_percent: int | None = None
    stage: str | None = None


class RenderIn(BaseModel):
    preset: str


class RenderOut(BaseModel):
    job_id: str
    preset: str


class DecisionJsonOut(BaseModel):
    file_id: str
    state_code: str
    state_label: str
    status_gate: str
    approval_required: bool
    risk_flags: list[str]
    decision_json: dict


class VisibilityIn(BaseModel):
    visibility: str = Field(..., pattern="^(private|public|hidden)$")


def _file_kind(content_type: str, filename: str) -> str:
    rule = get_rule_for_filename(filename)
    if rule:
        return rule.kind
    ctype = (content_type or "").strip().lower()
    if ctype.startswith("image/"):
        return "image"
    if ctype == "application/pdf":
        return "doc"
    return "3d"


def _build_file_urls(f: UploadFileModel) -> tuple[str | None, str | None, str | None]:
    if (_effective_status(f) or "").lower() != "ready":
        return None, None, None
    public_id = _public_file_id(f.file_id)
    if f.gltf_key:
        gltf_url = f"/api/v1/files/{public_id}/gltf"
        previews = _preview_urls(f)
        return (previews[0] if previews else gltf_url), gltf_url, None
    if _file_kind(f.content_type, f.original_filename) == "doc":
        if (f.meta or {}).get("pdf_key"):
            return f"/api/v1/files/{public_id}/pdf", None, f"/api/v1/files/{public_id}/pdf"
    original_url = f"/api/v1/files/{public_id}/content"
    return original_url, None, original_url


def _file_thumbnail_url(f: UploadFileModel) -> str | None:
    if not f.thumbnail_key or (_effective_status(f) or "").lower() != "ready":
        return None
    return f"/api/v1/files/{_public_file_id(f.file_id)}/thumbnail"


def _file_mode(f: UploadFileModel) -> str | None:
    meta = f.meta or {}
    raw_mode = meta.get("mode")
    if isinstance(raw_mode, str) and raw_mode:
        return raw_mode
    rule = get_rule_for_filename(f.original_filename)
    return rule.mode if rule else None


def _preview_urls(f: UploadFileModel) -> list[str]:
    if (_effective_status(f) or "").lower() != "ready":
        return []
    meta = f.meta or {}
    urls: list[str] = []
    preview_keys = meta.get("preview_jpg_keys")
    if isinstance(preview_keys, list):
        for idx, _key in enumerate(preview_keys):
            urls.append(f"/api/v1/files/{_public_file_id(f.file_id)}/preview/{idx}")
    elif isinstance(meta.get("pdf_key"), str):
        urls.append(f"/api/v1/files/{_public_file_id(f.file_id)}/pdf")
    elif f.thumbnail_key:
        urls.append(f"/api/v1/files/{_public_file_id(f.file_id)}/thumbnail")
    return urls


def _geometry_meta(f: UploadFileModel) -> dict[str, Any] | None:
    meta = f.meta or {}
    data = meta.get("geometry_meta_json")
    return data if isinstance(data, dict) else None


def _part_count_meta(f: UploadFileModel) -> int | None:
    meta = f.meta or {}
    value = meta.get("part_count")
    if isinstance(value, int):
        return value
    geometry = _geometry_meta(f) or {}
    gcount = geometry.get("part_count")
    if isinstance(gcount, int):
        return gcount
    return None


def _meets_ready_contract(f: UploadFileModel) -> bool:
    kind = _file_kind(f.content_type, f.original_filename)
    meta = f.meta if isinstance(f.meta, dict) else {}
    if kind == "3d":
        previews = meta.get("preview_jpg_keys")
        return bool(f.gltf_key and isinstance(meta.get("assembly_meta_key"), str) and isinstance(previews, list) and len(previews) >= 3)
    if kind == "doc":
        return bool(isinstance(meta.get("pdf_key"), str) and f.thumbnail_key)
    if kind in {"2d", "image"}:
        return bool(f.thumbnail_key)
    return True


def _effective_status(f: UploadFileModel) -> str:
    raw = (f.status or "").lower()
    if raw == "ready" and not _meets_ready_contract(f):
        return "failed"
    return f.status


def _serialize_file_out(f: UploadFileModel) -> FileOut:
    preview_url, gltf_url, original_url = _build_file_urls(f)
    previews = _preview_urls(f)
    effective_status = _effective_status(f)
    err = (f.meta or {}).get("error") if effective_status == "failed" else None
    if effective_status == "failed" and not err and (f.status or "").lower() == "ready":
        err = "assembly_meta_key and preview_jpg_keys are mandatory for ready status"
    return FileOut(
        file_id=_public_file_id(f.file_id),
        original_name=f.original_filename,
        kind=_file_kind(f.content_type, f.original_filename),
        mode=_file_mode(f),
        created_at=f.created_at,
        content_type=f.content_type,
        size_bytes=int(f.size_bytes),
        status=effective_status,
        visibility=f.visibility,
        thumbnail_url=_file_thumbnail_url(f),
        preview_url=preview_url,
        preview_urls=previews or None,
        gltf_url=gltf_url,
        original_url=original_url,
        bbox_meta=(_geometry_meta(f) or {}).get("bbox"),
        part_count=_part_count_meta(f),
        error=err,
    )


@router.post("/initiate", response_model=InitiateOut)
def initiate_upload(
    data: InitiateIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    _check_upload_rate(principal)
    if not data.filename:
        raise HTTPException(status_code=400, detail="filename required")
    _validate_upload(data.content_type, data.size_bytes, data.filename)

    owner_sub = principal.owner_sub or principal.user_id or ""
    if not owner_sub:
        raise HTTPException(status_code=401, detail="Unauthorized")
    bucket = settings.s3_bucket
    key = _safe_object_key(owner_sub)
    kind, mode = _derive_kind_mode(data.filename)
    file_meta = {"kind": kind, "mode": mode, "project_id": "default", "virus_scan_status": "queued"}

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
        folder_key=_derive_folder_key(data.filename, file_meta),
        meta=file_meta,
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
    return InitiateOut(file_id=_public_file_id(f.file_id), upload_url=url, expires_in_seconds=900)


@router.post("/upload", response_model=FileOut)
async def direct_upload(
    upload: UploadFile = FastAPIFile(...),
    project_id: str | None = Form(default=None),
    projectId: str | None = Form(default=None),
    db: Session = Depends(get_db),
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    _check_upload_rate(principal)
    if not upload.filename:
        raise HTTPException(status_code=400, detail="filename required")

    # Determine size without loading whole file into memory
    upload.file.seek(0, 2)
    size_bytes = upload.file.tell()
    upload.file.seek(0)

    content_type = (upload.content_type or "application/octet-stream").strip()

    # MIME sniff guard (first bytes only) to block extension spoofing.
    head = upload.file.read(8192)
    upload.file.seek(0)
    sniffed = infer_mime_from_bytes(head, upload.filename)
    _validate_upload(content_type, size_bytes, upload.filename, sniffed_content_type=sniffed)

    owner_sub = principal.owner_sub or principal.user_id or ""
    if not owner_sub:
        raise HTTPException(status_code=401, detail="Unauthorized")
    bucket = settings.s3_bucket
    key = _safe_object_key(owner_sub)
    kind, mode = _derive_kind_mode(upload.filename)
    effective_project_id = (project_id or projectId or "default").strip() or "default"
    file_meta = {
        "kind": kind,
        "mode": mode,
        "project_id": effective_project_id,
        "sniffed_content_type": sniffed,
        "virus_scan_status": "queued",
    }

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
        folder_key=_derive_folder_key(upload.filename, file_meta),
        meta=file_meta,
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
            f.meta = {**(f.meta or {}), "job_id": job_id, "project_id": effective_project_id}
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
        data={"filename": f.original_filename, "size_bytes": int(f.size_bytes), "project_id": effective_project_id},
    )
    db.commit()

    return _serialize_file_out(f)


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

    normalized_file_id = _normalize_file_id(file_id)
    f = _get_file_by_identifier(db, normalized_file_id)
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

    meta = f.meta if isinstance(f.meta, dict) else {}
    kind, mode = _derive_kind_mode(f.original_filename, meta)
    f.status = "queued"
    f.folder_key = f.folder_key or _derive_folder_key(f.original_filename, meta)
    f.meta = {
        **meta,
        "kind": kind,
        "mode": mode,
        "project_id": str(meta.get("project_id") or "default"),
        "virus_scan_status": str(meta.get("virus_scan_status") or "queued"),
    }
    f.updated_at = _now()
    db.add(f)
    db.commit()
    db.refresh(f)
    print(
        f"upload_completed file_id={f.file_id} object_key={f.object_key} "
        f"size_bytes={int(f.size_bytes)} content_type={f.content_type} "
        f"route=/api/v1/files/{normalized_file_id}/complete"
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
            f"redis_url={settings.REDIS_URL} route=/api/v1/files/{normalized_file_id}/complete"
        )
    except Exception as exc:
        print(
            f"enqueue_failed file_id={f.file_id} queue=cad job_id=None "
            f"redis_url={settings.REDIS_URL} route=/api/v1/files/{normalized_file_id}/complete error={exc}"
        )
        # If worker queue is down, keep status queued; client can retry later.
        job_id = None

    return _serialize_file_out(f)


@router.get("", response_model=Union[PageOut, RecentPageOut])
def list_files(
    page: int = 1,
    page_size: int = 20,
    include_hidden: bool = False,
    recent: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    if page < 1 or page_size < 1 or page_size > 100:
        raise HTTPException(status_code=400, detail="Invalid pagination")
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Invalid limit")

    owner_sub = principal.owner_sub or ""
    if principal.typ == "guest":
        q = db.query(UploadFileModel).filter(
            (UploadFileModel.owner_anon_sub == owner_sub) | (UploadFileModel.owner_sub == owner_sub)
        )
    else:
        q = db.query(UploadFileModel).filter(UploadFileModel.owner_user_id == principal.user_id)
    if not include_hidden:
        q = q.filter(UploadFileModel.visibility != "hidden")

    if bool(recent):
        rows = q.order_by(UploadFileModel.created_at.desc()).limit(limit).all()
        items = [
            RecentFileOut(
                file_id=_public_file_id(r.file_id),
                original_name=r.original_filename,
                kind=_file_kind(r.content_type, r.original_filename),
                status=r.status,
                created_at=r.created_at,
                thumbnail_url=_file_thumbnail_url(r),
            )
            for r in rows
        ]
        return RecentPageOut(items=items, limit=limit)

    total = q.count()
    rows = (
        q.order_by(UploadFileModel.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [_serialize_file_out(r) for r in rows]
    return PageOut(items=items, page=page, page_size=page_size, total=total)


@router.get("/{file_id}", response_model=FileDetailOut)
def get_file(
    file_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    f = _get_file_by_identifier(db, file_id)
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(f, principal)

    defaults = f.meta.get("defaults") if isinstance(f.meta, dict) and isinstance(f.meta.get("defaults"), dict) else {}
    payload = _serialize_file_out(f)
    return FileDetailOut(
        **payload.model_dump(),
        lods=_build_lod_map(f, include_key=False),
        quality_default=str(defaults.get("quality") or "Medium"),
        view_mode_default=str(defaults.get("view_mode") or "shaded_edge"),
    )


@router.get("/{file_id}/versions", response_model=FileVersionsOut)
def file_versions(
    file_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    f = _get_file_by_identifier(db, file_id)
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(f, principal)

    meta = f.meta if isinstance(f.meta, dict) else {}
    raw_versions = meta.get("versions")
    versions: list[FileVersionOut] = []
    if isinstance(raw_versions, list):
        for idx, item in enumerate(raw_versions):
            if not isinstance(item, dict):
                continue
            version_no = item.get("version_no")
            if not isinstance(version_no, int) or version_no < 1:
                version_no = idx + 1
            created_at = item.get("created_at")
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                except ValueError:
                    created_at = f.created_at
            if not isinstance(created_at, datetime):
                created_at = f.created_at
            status_value = item.get("status")
            status_text = str(status_value) if status_value is not None else _effective_status(f)
            versions.append(
                FileVersionOut(
                    version_no=version_no,
                    created_at=created_at,
                    status=status_text,
                )
            )

    if not versions:
        versions = [
            FileVersionOut(
                version_no=1,
                created_at=f.created_at,
                status=_effective_status(f),
            )
        ]

    versions.sort(key=lambda row: row.version_no)
    return FileVersionsOut(file_id=_public_file_id(f.file_id), versions=versions)


@router.get("/{file_id}/decision_json", response_model=DecisionJsonOut)
def file_decision_json(
    file_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    f = _get_file_by_identifier(db, file_id)
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(f, principal)

    rules = load_rule_config_map(db)
    decision_json = build_decision_json(f, rules)
    f.decision_json = decision_json
    f.meta = {**(f.meta or {}), "decision_json": decision_json}
    db.add(f)
    upsert_orchestrator_session(db, f, decision_json)
    db.commit()

    return DecisionJsonOut(
        file_id=_public_file_id(f.file_id),
        state_code=str(decision_json.get("state_code") or "S0"),
        state_label=str(decision_json.get("state_label") or "uploaded"),
        status_gate=str(decision_json.get("status_gate") or "PENDING"),
        approval_required=bool(decision_json.get("approval_required")),
        risk_flags=[str(item) for item in (decision_json.get("risk_flags") or [])],
        decision_json=decision_json,
    )


@router.get("/{file_id}/manifest")
def file_manifest(
    file_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    f = _get_file_by_identifier(db, file_id)
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(f, principal)
    lods = _build_lod_map(f, include_key=False)
    return _build_scx_manifest(f, lods)


@router.get("/{file_id}/scx")
def download_scx(
    file_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    f = _get_file_by_identifier(db, file_id)
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(f, principal)
    if f.status != "ready":
        raise HTTPException(status_code=409, detail="File not ready")

    lods = _build_lod_map(f, include_key=True)
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
    headers = {"Content-Disposition": f'attachment; filename="{_public_file_id(f.file_id)}.scx"'}
    return StreamingResponse(zip_buffer, media_type="application/zip", headers=headers)


@router.get("/{file_id}/status", response_model=StatusOut)
def file_status(
    file_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    f = _get_file_by_identifier(db, file_id)
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(f, principal)

    status = (_effective_status(f) or "").lower()
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
    preview_keys = (f.meta or {}).get("preview_jpg_keys")
    if isinstance(preview_keys, list) and preview_keys:
        derivatives.append("preview_jpg")
    if isinstance((f.meta or {}).get("assembly_meta_key"), str):
        derivatives.append("assembly_meta")
    if isinstance((f.meta or {}).get("pdf_key"), str):
        derivatives.append("pdf")
    if f.content_type.startswith("image/") or f.content_type == "application/pdf":
        if f.status == "ready":
            derivatives.append("original")
    if (f.original_filename or "").lower().endswith(".dxf"):
        if f.status == "ready":
            derivatives.append("dxf")

    progress_hint = None
    progress_percent: int | None = None
    stage: str | None = None
    if f.meta and isinstance(f.meta, dict):
        progress_hint = f.meta.get("progress")
        percent_raw = f.meta.get("progress_percent")
        stage_raw = f.meta.get("stage")
        if isinstance(percent_raw, int):
            progress_percent = max(0, min(100, percent_raw))
        if isinstance(stage_raw, str) and stage_raw.strip():
            stage = stage_raw.strip()
    if not progress_hint:
        progress_hint = f.status
    if progress_percent is None:
        if state == "queued":
            progress_percent = 5
        elif state == "running":
            progress_percent = 55
        elif state == "succeeded":
            progress_percent = 100
        elif state == "failed":
            progress_percent = 100

    return StatusOut(
        state=state,
        derivatives_available=derivatives,
        progress_hint=progress_hint,
        progress_percent=progress_percent,
        stage=stage,
    )


@router.post("/{file_id}/render", response_model=RenderOut)
def enqueue_render(
    file_id: str,
    data: RenderIn,
    db: Session = Depends(get_db),
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    f = _get_file_by_identifier(db, file_id)
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
    f = _get_file_by_identifier(db, file_id)
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
    f = _get_file_by_identifier(db, file_id)
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(f, principal)
    if f.status != "ready":
        raise HTTPException(status_code=409, detail="File not ready")

    s3 = s3_client()
    obj = s3.get_object(Bucket=f.bucket, Key=f.object_key)
    stream = obj["Body"].iter_chunks()
    return StreamingResponse(stream, media_type=f.content_type)


@router.get("/{file_id}/thumbnail")
def download_thumbnail(
    file_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    f = _get_file_by_identifier(db, file_id)
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(f, principal)
    if not f.thumbnail_key:
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    s3 = s3_client()
    obj = s3.get_object(Bucket=f.bucket, Key=f.thumbnail_key)
    stream = obj["Body"].iter_chunks()
    return StreamingResponse(stream, media_type="image/png")


@router.get("/{file_id}/preview/{index}")
def download_preview_jpg(
    file_id: str,
    index: int,
    db: Session = Depends(get_db),
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    f = _get_file_by_identifier(db, file_id)
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(f, principal)
    previews = (f.meta or {}).get("preview_jpg_keys")
    if not isinstance(previews, list) or index < 0 or index >= len(previews):
        raise HTTPException(status_code=404, detail="Preview not found")
    key = previews[index]
    if not isinstance(key, str) or not key:
        raise HTTPException(status_code=404, detail="Preview not found")
    s3 = s3_client()
    obj = s3.get_object(Bucket=f.bucket, Key=key)
    stream = obj["Body"].iter_chunks()
    return StreamingResponse(stream, media_type="image/jpeg")


@router.get("/{file_id}/pdf")
def download_pdf_content(
    file_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    f = _get_file_by_identifier(db, file_id)
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(f, principal)
    pdf_key = (f.meta or {}).get("pdf_key")
    if not isinstance(pdf_key, str) or not pdf_key:
        raise HTTPException(status_code=404, detail="PDF not found")
    s3 = s3_client()
    obj = s3.get_object(Bucket=f.bucket, Key=pdf_key)
    stream = obj["Body"].iter_chunks()
    return StreamingResponse(stream, media_type="application/pdf")


@router.get("/{file_id}/gltf")
def download_gltf(
    file_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    f = _get_file_by_identifier(db, file_id)
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
    if lod_name not in {"lod0", "lod1", "lod2"}:
        raise HTTPException(status_code=400, detail="Invalid LOD")
    f = _get_file_by_identifier(db, file_id)
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(f, principal)
    if f.status != "ready":
        raise HTTPException(status_code=409, detail="File not ready")

    lods = _build_lod_map(f, include_key=True)
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
    f = _get_file_by_identifier(db, file_id)
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(f, principal)

    f.visibility = data.visibility
    f.updated_at = _now()
    db.add(f)
    db.commit()
    db.refresh(f)

    return _serialize_file_out(f)


def _is_dxf(filename: str) -> bool:
    return (filename or "").lower().endswith(".dxf")


@router.get("/{file_id}/dxf/manifest")
def dxf_manifest(
    file_id: str,
    db: Session = Depends(get_db),
    principal: Principal = Depends(_require_principal),
):
    _feature_on()
    f = _get_file_by_identifier(db, file_id)
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
    f = _get_file_by_identifier(db, file_id)
    if not f:
        raise HTTPException(status_code=404, detail="File not found")
    _assert_file_access(f, principal)
    if f.status != "ready":
        raise HTTPException(status_code=409, detail="File not ready")
    if not _is_dxf(f.original_filename):
        raise HTTPException(status_code=415, detail="Not a DXF file")

    visible_layers = None
    if layers is not None:
        parsed_layers = {l.strip() for l in layers.split(",") if l.strip()}
        visible_layers = parsed_layers or None

    s3 = s3_client()
    obj = s3.get_object(Bucket=f.bucket, Key=f.object_key)
    with tempfile.NamedTemporaryFile(suffix=".dxf") as tmp:
        for chunk in obj["Body"].iter_chunks():
            tmp.write(chunk)
        tmp.flush()
        doc = load_doc(tmp.name)
    svg = render_svg(doc, visible_layers)
    return Response(content=svg, media_type="image/svg+xml")
