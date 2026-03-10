"""AgentEventBus — Redis Streams event bus for Agent OS.

Wraps RedisStreamsAdapter. Provides publish / consume / health.
Falls back to no-op when Redis is unavailable (dev/test mode).
"""
from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from typing import Any

from app.events.cloudevents import CloudEvent

log = logging.getLogger(__name__)

_AGENT_STREAM_KEY = os.getenv("AGENT_EVENT_STREAM", "stellcodex:agent:events")


def _make_redis() -> Any | None:
    try:
        from redis import Redis
        from app.core.config import settings
        url = getattr(settings, "REDIS_URL", None) or os.getenv("REDIS_URL", "")
        if not url:
            return None
        return Redis.from_url(url, decode_responses=True, socket_connect_timeout=2)
    except Exception as exc:
        log.warning("agent_event_bus.redis_unavailable: %s", exc)
        return None


class AgentEventBus:
    """Publish-capable event bus for the Agent OS layer."""

    def __init__(self, stream_key: str = _AGENT_STREAM_KEY) -> None:
        self.stream_key = stream_key
        self._redis = _make_redis()
        self._published: list[CloudEvent] = []  # in-memory fallback / test capture

    @property
    def redis_available(self) -> bool:
        if self._redis is None:
            return False
        try:
            self._redis.ping()
            return True
        except Exception:
            return False

    def publish(self, event: CloudEvent) -> str:
        """Publish a CloudEvent. Returns message id."""
        if self._redis is not None:
            try:
                from app.events.adapters.redis_streams import RedisStreamsAdapter
                adapter = RedisStreamsAdapter(self._redis, self.stream_key)
                msg_id = adapter.xadd(event.to_wire())
                self._published.append(event)
                log.debug("bus.published event_id=%s type=%s", event.id, event.type)
                return msg_id
            except Exception as exc:
                log.warning("bus.redis_publish_failed: %s — falling back to memory", exc)
        self._published.append(event)
        log.debug("bus.memory_published event_id=%s type=%s", event.id, event.type)
        return event.id

    def publish_raw(
        self,
        *,
        event_type: str,
        source: str,
        subject: str,
        tenant_id: str,
        project_id: str,
        data: dict[str, Any] | None = None,
        trace_id: str | None = None,
        event_id: str | None = None,
    ) -> CloudEvent:
        event = CloudEvent.build(
            event_type=event_type,
            source=source,
            subject=subject,
            tenant_id=str(tenant_id),
            project_id=str(project_id),
            data=data,
            trace_id=trace_id,
            event_id=event_id,
        )
        self.publish(event)
        return event

    def drain(self) -> list[CloudEvent]:
        """Return and clear in-memory published events (for testing)."""
        events = list(self._published)
        self._published.clear()
        return events

    def health(self) -> dict[str, Any]:
        return {
            "stream_key": self.stream_key,
            "redis_available": self.redis_available,
            "memory_queue_len": len(self._published),
        }


@lru_cache(maxsize=1)
def get_agent_event_bus() -> AgentEventBus:
    return AgentEventBus()
