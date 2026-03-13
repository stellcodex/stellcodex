"""Idempotency guard — prevent duplicate event processing.

Uses consumer-scoped records in the canonical `processed_event_ids` table.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.phase2 import ProcessedEventId

log = logging.getLogger(__name__)

DEFAULT_CONSUMER = "events.default"


def is_already_processed(db: Session, event_id: str, consumer: str = DEFAULT_CONSUMER) -> bool:
    """Return True if this event_id was already processed by this consumer."""
    return (
        db.query(ProcessedEventId)
        .filter(
            ProcessedEventId.event_id == str(event_id),
            ProcessedEventId.consumer == str(consumer or DEFAULT_CONSUMER),
        )
        .first()
        is not None
    )


def mark_processed(
    db: Session,
    event_id: str,
    event_type: str = "",
    *,
    consumer: str = DEFAULT_CONSUMER,
    file_id: str | None = None,
    version_no: int | None = None,
    trace_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> None:
    """Record event_id as processed for a consumer. Caller must commit."""
    existing = (
        db.query(ProcessedEventId)
        .filter(
            ProcessedEventId.event_id == str(event_id),
            ProcessedEventId.consumer == str(consumer or DEFAULT_CONSUMER),
        )
        .first()
    )
    if existing:
        return
    record = ProcessedEventId(
        event_id=str(event_id),
        event_type=str(event_type),
        consumer=str(consumer or DEFAULT_CONSUMER),
        file_id=str(file_id or "") or None,
        version_no=int(version_no) if version_no is not None else None,
        trace_id=str(trace_id or "") or None,
        payload=payload if isinstance(payload, dict) else {},
        processed_at=datetime.utcnow(),
    )
    db.add(record)
    log.debug("idempotency.mark_processed event_id=%s consumer=%s", event_id, consumer)


def ensure_idempotent(
    db: Session,
    event_id: str,
    event_type: str = "",
    *,
    consumer: str = DEFAULT_CONSUMER,
    file_id: str | None = None,
    version_no: int | None = None,
    trace_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> bool:
    """Check-and-mark in one call. Returns True if ALREADY processed (skip).
    Returns False if this is a new event (proceed and caller must commit).
    """
    scoped_consumer = str(consumer or DEFAULT_CONSUMER)
    if is_already_processed(db, event_id, scoped_consumer):
        log.debug("idempotency.duplicate_skipped event_id=%s consumer=%s", event_id, scoped_consumer)
        return True
    mark_processed(
        db,
        event_id,
        event_type,
        consumer=scoped_consumer,
        file_id=file_id,
        version_no=version_no,
        trace_id=trace_id,
        payload=payload,
    )
    return False
