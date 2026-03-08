from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.master_contract import FileVersion
from app.models.phase2 import ProcessedEventId, StageLock


def resolve_version_no(db: Session, file_id: str) -> int:
    row = (
        db.query(FileVersion)
        .filter(FileVersion.file_id == file_id)
        .order_by(FileVersion.version_no.desc())
        .first()
    )
    if row is None:
        return 1
    value = int(row.version_no or 1)
    return value if value > 0 else 1


def is_processed(db: Session, event_id: str, consumer: str) -> bool:
    row = (
        db.query(ProcessedEventId)
        .filter(
            ProcessedEventId.event_id == event_id,
            ProcessedEventId.consumer == consumer,
        )
        .first()
    )
    return row is not None


def mark_processed(
    db: Session,
    *,
    event_id: str,
    event_type: str,
    consumer: str,
    file_id: str,
    version_no: int,
    trace_id: str,
    payload: dict[str, Any],
) -> ProcessedEventId:
    row = ProcessedEventId(
        event_id=event_id,
        event_type=event_type,
        consumer=consumer,
        file_id=file_id,
        version_no=version_no,
        trace_id=trace_id,
        payload=payload if isinstance(payload, dict) else {},
    )
    db.add(row)
    return row


def acquire_stage_lock(db: Session, *, file_id: str, version_no: int, stage: str, ttl_seconds: int = 1200) -> str | None:
    now = datetime.utcnow()
    token = uuid4().hex
    row = (
        db.query(StageLock)
        .filter(
            StageLock.file_id == file_id,
            StageLock.version_no == int(version_no),
            StageLock.stage == stage,
        )
        .first()
    )
    if row is None:
        row = StageLock(
            file_id=file_id,
            version_no=int(version_no),
            stage=stage,
            lock_token=token,
            locked_at=now,
            expires_at=now + timedelta(seconds=max(30, int(ttl_seconds))),
        )
        db.add(row)
        return token

    if row.expires_at and row.expires_at > now and row.lock_token:
        return None

    row.lock_token = token
    row.locked_at = now
    row.expires_at = now + timedelta(seconds=max(30, int(ttl_seconds)))
    db.add(row)
    return token


def release_stage_lock(db: Session, *, file_id: str, version_no: int, stage: str, lock_token: str) -> None:
    row = (
        db.query(StageLock)
        .filter(
            StageLock.file_id == file_id,
            StageLock.version_no == int(version_no),
            StageLock.stage == stage,
        )
        .first()
    )
    if row is None:
        return
    if row.lock_token != lock_token:
        return
    db.delete(row)
