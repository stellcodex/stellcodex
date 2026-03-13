from __future__ import annotations

import os
from typing import Any

from redis import Redis

from app.core.config import settings
from app.core.events import EventEnvelope


DEFAULT_STREAM_KEY = os.getenv("PHASE2_EVENT_STREAM", "stellcodex:phase2:events")


def _redis_client() -> Redis | None:
    redis_url = settings.REDIS_URL
    if not redis_url:
        return None
    return Redis.from_url(redis_url, decode_responses=True)


class EventBus:
    def __init__(self, stream_key: str = DEFAULT_STREAM_KEY) -> None:
        self.stream_key = stream_key
        self.redis = _redis_client()

    def publish(self, envelope: EventEnvelope) -> str:
        message_id = envelope.id
        if self.redis is not None:
            message_id = str(self.redis.xadd(self.stream_key, envelope.to_wire()))
        _dispatch_knowledge_ingestion(envelope)
        return message_id

    def publish_event(
        self,
        *,
        event_type: str,
        source: str,
        subject: str,
        tenant_id: str,
        project_id: str,
        trace_id: str | None = None,
        event_id: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> EventEnvelope:
        envelope = EventEnvelope.build(
            event_type=event_type,
            source=source,
            subject=subject,
            tenant_id=tenant_id,
            project_id=project_id,
            trace_id=trace_id,
            event_id=event_id,
            data=data,
        )
        self.publish(envelope)
        return envelope

    def fetch_recent(self, limit: int = 50) -> list[EventEnvelope]:
        if self.redis is None:
            return []
        rows = self.redis.xrevrange(self.stream_key, count=max(1, limit))
        out: list[EventEnvelope] = []
        for _message_id, fields in reversed(rows):
            try:
                out.append(EventEnvelope.from_wire(fields))
            except Exception:
                continue
        return out


def default_event_bus() -> EventBus:
    return EventBus()


def _dispatch_knowledge_ingestion(envelope: EventEnvelope) -> None:
    try:
        from app.knowledge.worker import ingest_event

        ingest_event(envelope)
    except Exception:
        # Event production must not fail if knowledge indexing path has issues.
        return
