from __future__ import annotations

from typing import Any

from app.core.events import EventEnvelope
from app.db.session import SessionLocal
from app.knowledge.service import get_knowledge_service


def _to_envelope(payload: EventEnvelope | dict[str, Any]) -> EventEnvelope:
    if isinstance(payload, EventEnvelope):
        return payload
    if not isinstance(payload, dict):
        raise ValueError("knowledge worker payload must be EventEnvelope or dict")
    return EventEnvelope.from_dict(payload)


def ingest_event(payload: EventEnvelope | dict[str, Any]) -> dict[str, Any]:
    envelope = _to_envelope(payload)
    db = SessionLocal()
    try:
        result = get_knowledge_service().ingest_event(db=db, envelope=envelope)
        db.commit()
        return result
    except Exception as exc:
        db.rollback()
        return {"status": "failed", "failure_code": "INDEX_WRITE_FAIL", "error": str(exc), "event_id": envelope.id}
    finally:
        db.close()
