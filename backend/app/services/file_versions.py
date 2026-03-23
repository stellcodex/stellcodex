from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.file import UploadFile
from app.models.file_version import FileVersion

SAFE_META_FIELDS = {
    "kind",
    "mode",
    "project_id",
    "rule_version",
    "generated_by",
    "part_count",
    "geometry_meta_json",
    "geometry_report",
    "dfm_findings",
    "decision_json",
}


def _safe_meta_snapshot(meta: dict[str, Any] | None) -> dict[str, Any]:
    payload = meta if isinstance(meta, dict) else {}
    return {key: payload[key] for key in SAFE_META_FIELDS if key in payload}


def get_current_file_version(db: Session, file_id: str) -> FileVersion | None:
    return (
        db.query(FileVersion)
        .filter(FileVersion.file_id == file_id, FileVersion.is_current.is_(True))
        .order_by(FileVersion.version_number.desc())
        .first()
    )


def list_file_versions(db: Session, file_id: str) -> list[FileVersion]:
    return (
        db.query(FileVersion)
        .filter(FileVersion.file_id == file_id)
        .order_by(FileVersion.version_number.desc(), FileVersion.created_at.desc())
        .all()
    )


def _next_version_number(db: Session, file_id: str) -> int:
    current = db.query(func.max(FileVersion.version_number)).filter(FileVersion.file_id == file_id).scalar()
    return int(current or 0) + 1


def sync_current_file_version(
    db: Session,
    file_row: UploadFile,
    *,
    created_by_user_id: str | None = None,
) -> FileVersion:
    version = get_current_file_version(db, file_row.file_id)
    snapshot = _safe_meta_snapshot(file_row.meta)
    if version is None:
        version = FileVersion(
            id=uuid.uuid4(),
            file_id=file_row.file_id,
            version_number=_next_version_number(db, file_row.file_id),
            created_by_user_id=created_by_user_id,
            original_filename=file_row.original_filename,
            content_type=file_row.content_type,
            size_bytes=int(file_row.size_bytes),
            sha256=file_row.sha256,
            bucket=file_row.bucket,
            object_key=file_row.object_key,
            status=file_row.status,
            is_current=True,
            meta=snapshot,
        )
    else:
        version.created_by_user_id = version.created_by_user_id or created_by_user_id
        version.original_filename = file_row.original_filename
        version.content_type = file_row.content_type
        version.size_bytes = int(file_row.size_bytes)
        version.sha256 = file_row.sha256
        version.bucket = file_row.bucket
        version.object_key = file_row.object_key
        version.status = file_row.status
        version.is_current = True
        version.meta = snapshot
    db.add(version)
    return version


def create_new_file_version(
    db: Session,
    *,
    file_row: UploadFile,
    created_by_user_id: str | None,
    original_filename: str,
    content_type: str,
    size_bytes: int,
    sha256: str | None,
    bucket: str,
    object_key: str,
    status: str,
    meta: dict[str, Any] | None = None,
) -> FileVersion:
    current = get_current_file_version(db, file_row.file_id)
    if current is not None:
        current.is_current = False
        db.add(current)

    version = FileVersion(
        id=uuid.uuid4(),
        file_id=file_row.file_id,
        version_number=_next_version_number(db, file_row.file_id),
        created_by_user_id=created_by_user_id,
        original_filename=original_filename,
        content_type=content_type,
        size_bytes=int(size_bytes),
        sha256=sha256,
        bucket=bucket,
        object_key=object_key,
        status=status,
        is_current=True,
        meta=_safe_meta_snapshot(meta),
    )
    db.add(version)
    return version
