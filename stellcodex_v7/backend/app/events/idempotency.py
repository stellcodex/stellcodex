"""Idempotency guard — prevent duplicate event processing.

Uses the existing `processed_event_ids` table in PostgreSQL.
"""
from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.phase2 import ProcessedEventId

log = logging.getLogger(__name__)


def is_already_processed(db: Session, event_id: str) -> bool:
    """Return True if this event_id was already processed."""
    return (
        db.query(ProcessedEventId)
        .filter(ProcessedEventId.event_id == str(event_id))
        .first()
        is not None
    )


def mark_processed(db: Session, event_id: str, event_type: str = "") -> None:
    """Record event_id as processed. Caller must commit."""
    existing = (
        db.query(ProcessedEventId)
        .filter(ProcessedEventId.event_id == str(event_id))
        .first()
    )
    if existing:
        return
    record = ProcessedEventId(
        event_id=str(event_id),
        event_type=str(event_type),
        processed_at=datetime.utcnow(),
    )
    db.add(record)
    log.debug("idempotency.mark_processed event_id=%s", event_id)


def ensure_idempotent(db: Session, event_id: str, event_type: str = "") -> bool:
    """Check-and-mark in one call. Returns True if ALREADY processed (skip).
    Returns False if this is a new event (proceed and caller must commit).
    """
    if is_already_processed(db, event_id):
        log.debug("idempotency.duplicate_skipped event_id=%s", event_id)
        return True
    mark_processed(db, event_id, event_type)
    return False
