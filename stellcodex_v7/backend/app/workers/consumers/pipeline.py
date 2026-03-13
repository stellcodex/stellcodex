from __future__ import annotations

import time
from typing import Any, Callable, Dict

from sqlalchemy.orm import Session

from app.core.artifact_cache import cache_hit, get_manifest_row, get_manifest_row_by_geometry, stable_hash, upsert_manifest
from app.core.dlq import StageExecutionError, record_dead_letter
from app.core.event_bus import EventBus
from app.core.events import EventEnvelope
from app.workers.consumers.common import acquire_stage_lock, is_processed, mark_processed, release_stage_lock


StageHandler = Callable[[Session, EventEnvelope, int], Dict[str, Any]]


def consume_with_guards(
    db: Session,
    bus: EventBus,
    *,
    envelope: EventEnvelope,
    consumer_name: str,
    stage: str,
    max_retries: int,
    failure_code: str,
    handler: StageHandler,
) -> dict[str, Any]:
    file_id = str(envelope.data.get("file_id") or "")
    version_no = int(envelope.data.get("version_no") or 1)
    geometry_hash = str(envelope.data.get("geometry_hash") or "").strip() or None
    if not file_id:
        raise ValueError("event payload missing file_id")

    if is_processed(db, envelope.id, consumer_name):
        return {"status": "duplicate", "file_id": file_id, "version_no": version_no, "stage": stage}

    lock_token = acquire_stage_lock(db, file_id=file_id, version_no=version_no, stage=stage)
    if lock_token is None:
        return {"status": "locked", "file_id": file_id, "version_no": version_no, "stage": stage}

    try:
        input_hash = stable_hash(envelope.data)
        if geometry_hash:
            row = get_manifest_row_by_geometry(
                db,
                file_id=file_id,
                version_no=version_no,
                stage=stage,
                geometry_hash=geometry_hash,
            )
        else:
            row = get_manifest_row(db, file_id, version_no, stage)
        if row is not None and row.input_hash == input_hash and str(row.status).lower() == "ready":
            cache_hit(db, row=row, file_id=file_id, version_no=version_no, stage=stage)
            mark_processed(
                db,
                event_id=envelope.id,
                event_type=envelope.type,
                consumer=consumer_name,
                file_id=file_id,
                version_no=version_no,
                trace_id=envelope.trace_id,
                payload=envelope.to_dict(),
            )
            db.commit()
            return {
                "status": "cache_hit",
                "file_id": file_id,
                "version_no": version_no,
                "stage": stage,
                "payload": row.artifact_payload if isinstance(row.artifact_payload, dict) else {},
            }

        attempt = max(0, int(envelope.data.get("retry_count") or 0))
        while True:
            try:
                output = handler(db, envelope, version_no)
                output_payload = output if isinstance(output, dict) else {}
                output_geometry_hash = str(output_payload.get("geometry_hash") or geometry_hash or "").strip() or None
                artifact_uri = output_payload.get("artifact_uri") if isinstance(output_payload.get("artifact_uri"), str) else None
                upsert_manifest(
                    db,
                    file_id=file_id,
                    version_no=version_no,
                    stage=stage,
                    geometry_hash=output_geometry_hash,
                    input_hash=input_hash,
                    artifact_uri=artifact_uri,
                    artifact_payload=output_payload,
                )
                mark_processed(
                    db,
                    event_id=envelope.id,
                    event_type=envelope.type,
                    consumer=consumer_name,
                    file_id=file_id,
                    version_no=version_no,
                    trace_id=envelope.trace_id,
                    payload=envelope.to_dict(),
                )
                db.commit()
                return {
                    "status": "processed",
                    "file_id": file_id,
                    "version_no": version_no,
                    "stage": stage,
                    "payload": output_payload,
                }
            except StageExecutionError as exc:
                db.rollback()
                if exc.transient and attempt < max_retries:
                    attempt += 1
                    backoff = 2 ** attempt
                    time.sleep(backoff)
                    continue
                record_dead_letter(
                    db,
                    bus,
                    envelope=envelope,
                    stage=stage,
                    failure_code=exc.failure_code or failure_code,
                    error_detail=str(exc),
                    retry_count=attempt,
                    payload_json=envelope.to_dict(),
                )
                return {
                    "status": "failed",
                    "file_id": file_id,
                    "version_no": version_no,
                    "stage": stage,
                    "error": str(exc),
                    "failure_code": exc.failure_code or failure_code,
                }
            except Exception as exc:
                db.rollback()
                record_dead_letter(
                    db,
                    bus,
                    envelope=envelope,
                    stage=stage,
                    failure_code=failure_code,
                    error_detail=str(exc),
                    retry_count=attempt,
                    payload_json=envelope.to_dict(),
                )
                return {
                    "status": "failed",
                    "file_id": file_id,
                    "version_no": version_no,
                    "stage": stage,
                    "error": str(exc),
                    "failure_code": failure_code,
                }
    finally:
        try:
            release_stage_lock(db, file_id=file_id, version_no=version_no, stage=stage, lock_token=lock_token)
            db.commit()
        except Exception:
            db.rollback()
