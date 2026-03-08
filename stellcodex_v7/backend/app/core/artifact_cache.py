from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.phase2 import ArtifactManifest
from app.services.audit import log_event


def stable_hash(payload: dict[str, Any] | None) -> str:
    encoded = json.dumps(payload or {}, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def get_manifest_row(db: Session, file_id: str, version_no: int, stage: str) -> ArtifactManifest | None:
    return (
        db.query(ArtifactManifest)
        .filter(
            ArtifactManifest.file_id == file_id,
            ArtifactManifest.version_no == int(version_no),
            ArtifactManifest.stage == stage,
        )
        .first()
    )


def cache_hit(
    db: Session,
    *,
    row: ArtifactManifest,
    file_id: str,
    version_no: int,
    stage: str,
) -> None:
    row.cache_hit_count = int(row.cache_hit_count or 0) + 1
    row.updated_at = datetime.utcnow()
    db.add(row)
    log_event(
        db,
        "artifact.cache.hit",
        file_id=file_id,
        data={
            "file_id": file_id,
            "version_no": int(version_no),
            "stage": stage,
            "cache_hit_count": row.cache_hit_count,
        },
    )


def upsert_manifest(
    db: Session,
    *,
    file_id: str,
    version_no: int,
    stage: str,
    input_hash: str,
    artifact_uri: str | None,
    artifact_payload: dict[str, Any] | None,
) -> ArtifactManifest:
    row = get_manifest_row(db, file_id, version_no, stage)
    payload = artifact_payload if isinstance(artifact_payload, dict) else {}
    payload_hash = stable_hash(payload)
    if row is None:
        row = ArtifactManifest(
            file_id=file_id,
            version_no=int(version_no),
            stage=stage,
            input_hash=input_hash,
            artifact_hash=payload_hash,
            artifact_uri=artifact_uri,
            artifact_payload=payload,
            status="ready",
        )
        db.add(row)
        return row

    # Input hash changed in same file/version/stage: mark stale.
    if row.input_hash != input_hash:
        log_event(
            db,
            "artifact.cache.stale",
            file_id=file_id,
            data={
                "file_id": file_id,
                "version_no": int(version_no),
                "stage": stage,
                "previous_input_hash": row.input_hash,
                "next_input_hash": input_hash,
            },
        )

    row.input_hash = input_hash
    row.artifact_hash = payload_hash
    row.artifact_uri = artifact_uri
    row.artifact_payload = payload
    row.status = "ready"
    row.updated_at = datetime.utcnow()
    db.add(row)
    return row
