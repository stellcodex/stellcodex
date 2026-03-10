"""Dead Letter Queue — routes exhausted-retry events to DLQ.

Wraps the existing DlqRecord model and adds Redis Streams DLQ support.
"""
from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.phase2 import DlqRecord

log = logging.getLogger(__name__)

_DLQ_STREAM = "stellcodex:events:dlq"


def send_to_dlq(
    *,
    db: Session,
    event_id: str,
    event_type: str,
    payload: dict[str, Any],
    failure_reason: str,
    retry_count: int,
    redis_adapter: Any | None = None,
) -> str:
    """Persist to DB DLQ and optionally publish to Redis DLQ stream."""
    record = DlqRecord(
        id=uuid.uuid4(),
        event_id=str(event_id),
        event_type=str(event_type),
        payload=payload,
        failure_reason=str(failure_reason),
        retry_count=int(retry_count),
        created_at=datetime.utcnow(),
    )
    db.add(record)
    log.warning(
        "dlq.sent event_id=%s type=%s reason=%s retries=%d",
        event_id, event_type, failure_reason, retry_count,
    )

    if redis_adapter is not None:
        try:
            redis_adapter.xadd_dlq(
                _DLQ_STREAM,
                {
                    "event_id": event_id,
                    "event_type": event_type,
                    "failure_reason": failure_reason,
                    "retry_count": str(retry_count),
                    "payload": json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                },
            )
        except Exception as exc:
            log.error("dlq.redis_write_failed: %s", exc)

    return str(record.id)


def get_dlq_count(db: Session) -> int:
    """Return total DLQ record count."""
    return db.query(DlqRecord).count()
