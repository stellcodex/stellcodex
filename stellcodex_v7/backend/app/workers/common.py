from __future__ import annotations

import base64
import json
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.ids import normalize_scx_id
from ..db import SessionLocal
from ..models.core import Artifact, ArtifactType, Job, JobStatus
from ..models.file import UploadFile as UploadFileModel
from ..storage import Storage, artifact_path_for_2d, artifact_path_for_3d, artifact_path_for_render
from app.core.config import settings
from app.core.storage import get_s3_client


WEBP_1X1 = base64.b64decode(
    "UklGRiIAAABXRUJQVlA4IBgAAAAwAQCdASoIAAgAAkA4JaQAA3AA/vuUAAA="
)


def minimal_pdf_bytes() -> bytes:
    objects = []
    def obj(num: int, body: str) -> str:
        return f"{num} 0 obj\n{body}\nendobj\n"

    objects.append(obj(1, "<< /Type /Catalog /Pages 2 0 R >>"))
    objects.append(obj(2, "<< /Type /Pages /Kids [3 0 R] /Count 1 >>"))
    objects.append(obj(3, "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>"))

    content = "%PDF-1.4\n"
    offsets = [0]
    for o in objects:
        offsets.append(len(content))
        content += o

    xref_offset = len(content)
    content += f"xref\n0 {len(offsets)}\n"
    content += "0000000000 65535 f \n"
    for off in offsets[1:]:
        content += f"{off:010d} 00000 n \n"
    content += "trailer\n<< /Size %d /Root 1 0 R >>\n" % len(offsets)
    content += "startxref\n%d\n%%EOF\n" % xref_offset
    return content.encode("ascii")


def write_artifact(
    db: Session,
    rev_uid,
    art_type: ArtifactType,
    blob_path: str,
    content_type: str,
    size: int | None = None,
) -> Artifact:
    artifact = (
        db.query(Artifact)
        .filter(Artifact.rev_uid == rev_uid, Artifact.type == art_type)
        .one_or_none()
    )
    if artifact is None:
        artifact = Artifact(
            rev_uid=rev_uid,
            type=art_type,
            blob_path=blob_path,
            content_type=content_type,
            ready=True,
            size=str(size) if size is not None else None,
        )
        db.add(artifact)
    else:
        artifact.blob_path = blob_path
        artifact.content_type = content_type
        artifact.ready = True
        if size is not None:
            artifact.size = str(size)
    return artifact


def mark_job_running(db: Session, job: Job) -> None:
    job.status = JobStatus.RUNNING
    job.started_at = datetime.utcnow()


def mark_job_done(db: Session, job: Job) -> None:
    job.status = JobStatus.SUCCEEDED
    job.finished_at = datetime.utcnow()


def mark_job_failed(db: Session, job: Job, error: str) -> None:
    job.status = JobStatus.FAILED
    job.error = error
    job.finished_at = datetime.utcnow()


def build_basic_meta(rev_uid: str) -> bytes:
    return json.dumps({"rev_uid": str(rev_uid), "generated_at": datetime.utcnow().isoformat()}).encode("utf-8")


def build_basic_tree() -> bytes:
    data = {
        "nodes": [
            {
                "id": "root",
                "name": "root",
                "parent": None,
                "children": [],
                "transform": [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
                "kind": "assembly",
                "mesh_ref": None,
            }
        ],
        "meshes": [],
    }
    return json.dumps(data).encode("utf-8")


def write_drawing_artifacts(db: Session, storage: Storage, project_id: str, rev_uid: str) -> None:
    svg_key = artifact_path_for_2d(project_id, rev_uid, "drawing.svg")
    pdf_key = artifact_path_for_2d(project_id, rev_uid, "drawing.pdf")
    meta_key = artifact_path_for_2d(project_id, rev_uid, "meta.json")
    thumb_key = artifact_path_for_2d(project_id, rev_uid, "thumb.webp")

    svg_bytes = b"<svg xmlns='http://www.w3.org/2000/svg' width='100' height='100'></svg>"
    pdf_bytes = minimal_pdf_bytes()
    meta_bytes = build_basic_meta(rev_uid)
    thumb_bytes = WEBP_1X1

    storage.write_bytes(svg_key, svg_bytes)
    storage.write_bytes(pdf_key, pdf_bytes)
    storage.write_bytes(meta_key, meta_bytes)
    storage.write_bytes(thumb_key, thumb_bytes)

    _upload_if_enabled(svg_key, svg_bytes, "image/svg+xml")
    _upload_if_enabled(pdf_key, pdf_bytes, "application/pdf")
    _upload_if_enabled(meta_key, meta_bytes, "application/json")
    _upload_if_enabled(thumb_key, thumb_bytes, "image/webp")

    write_artifact(db, rev_uid, ArtifactType.DRAWING_SVG, svg_key, "image/svg+xml", len(svg_bytes))
    write_artifact(db, rev_uid, ArtifactType.DRAWING_PDF, pdf_key, "application/pdf", len(pdf_bytes))
    write_artifact(db, rev_uid, ArtifactType.DRAWING_META, meta_key, "application/json", len(meta_bytes))
    write_artifact(db, rev_uid, ArtifactType.DRAWING_THUMB, thumb_key, "image/webp", len(thumb_bytes))


def write_render_artifact(db: Session, storage: Storage, project_id: str, rev_uid: str) -> None:
    render_key = artifact_path_for_render(project_id, rev_uid, "render.webp")
    storage.write_bytes(render_key, WEBP_1X1)
    _upload_if_enabled(render_key, WEBP_1X1, "image/webp")
    write_artifact(db, rev_uid, ArtifactType.RENDER_WEBP, render_key, "image/webp", len(WEBP_1X1))


def write_3d_artifacts(db: Session, storage: Storage, project_id: str, rev_uid: str, source_path: Path) -> None:
    lod0_key = artifact_path_for_3d(project_id, rev_uid, "lod0.glb")
    tree_key = artifact_path_for_3d(project_id, rev_uid, "tree.json")
    meta_key = artifact_path_for_3d(project_id, rev_uid, "meta.json")
    thumb_key = artifact_path_for_3d(project_id, rev_uid, "thumb.webp")

    storage.copy_from(source_path, lod0_key)
    tree_bytes = build_basic_tree()
    meta_bytes = build_basic_meta(rev_uid)
    thumb_bytes = WEBP_1X1

    storage.write_bytes(tree_key, tree_bytes)
    storage.write_bytes(meta_key, meta_bytes)
    storage.write_bytes(thumb_key, thumb_bytes)

    _upload_file_if_enabled(storage, lod0_key, "model/gltf-binary")
    _upload_if_enabled(tree_key, tree_bytes, "application/json")
    _upload_if_enabled(meta_key, meta_bytes, "application/json")
    _upload_if_enabled(thumb_key, thumb_bytes, "image/webp")

    print(f"wrote lod0.glb key={lod0_key}")
    print(f"wrote meta.json key={meta_key}")
    print(f"wrote thumb.webp key={thumb_key}")

    write_artifact(db, rev_uid, ArtifactType.LOD0_GLB, lod0_key, "model/gltf-binary", source_path.stat().st_size)
    write_artifact(db, rev_uid, ArtifactType.TREE_JSON, tree_key, "application/json", len(tree_bytes))
    write_artifact(db, rev_uid, ArtifactType.META_JSON, meta_key, "application/json", len(meta_bytes))
    write_artifact(db, rev_uid, ArtifactType.THUMB_WEBP, thumb_key, "image/webp", len(thumb_bytes))
    _sync_legacy_upload_ready(db, project_id, rev_uid, lod0_key, thumb_key)


def get_session():
    return SessionLocal()


def _upload_if_enabled(key: str, data: bytes, content_type: str) -> None:
    if not settings.s3_enabled:
        return
    s3 = get_s3_client(settings)
    s3.put_object(Bucket=settings.s3_bucket, Key=key, Body=data, ContentType=content_type)


def _upload_file_if_enabled(storage: Storage, key: str, content_type: str) -> None:
    if not settings.s3_enabled:
        return
    s3 = get_s3_client(settings)
    s3.upload_file(str(storage.root / key), settings.s3_bucket, key, ExtraArgs={"ContentType": content_type})


def _sync_legacy_upload_ready(
    db: Session,
    project_id: str,
    rev_uid: str,
    lod0_key: str,
    thumb_key: str,
) -> None:
    file_id = normalize_scx_id(str(rev_uid))
    row = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
    if row is None:
        return

    existing_meta = row.meta or {}
    legacy_mapping = existing_meta.get("legacy_mapping") if isinstance(existing_meta.get("legacy_mapping"), dict) else {}
    existing_lods = existing_meta.get("lods") if isinstance(existing_meta.get("lods"), dict) else {}
    row.gltf_key = lod0_key
    row.thumbnail_key = thumb_key
    row.status = "ready"
    row.meta = {
        **existing_meta,
        "legacy_mapping": {
            **legacy_mapping,
            "project_id": str(project_id),
            "rev_uid": str(rev_uid),
            "model_prefix": f"models/{project_id}/{rev_uid}/",
        },
        "defaults": {"view_mode": "shaded_edge", "quality": "Ultra", "camera": "iso_default"},
        "lods": {
            **existing_lods,
            "lod0": {"key": lod0_key, "ready": True},
            "lod1": {"key": (existing_lods.get("lod1") or {}).get("key"), "ready": False},
            "lod2": {"key": (existing_lods.get("lod2") or {}).get("key"), "ready": False},
        },
    }
    db.add(row)
