"""Event consumer — Redis Streams XREADGROUP with retry and DLQ routing.

Retry limit = 3. After exhaustion → DLQ.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.events.adapters.redis_streams import RedisStreamsAdapter
from app.events.cloudevents import CloudEvent
from app.events.dlq import send_to_dlq
from app.events.idempotency import ensure_idempotent

log = logging.getLogger(__name__)

_RETRY_LIMIT = 3
_RETRY_BACKOFF_SECONDS = [1, 3, 8]  # exponential-ish


EventHandler = Callable[[CloudEvent, Session], None]


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


class StreamConsumer:
    """Consumer that reads from a Redis Stream group, handles retries and DLQ."""

    def __init__(
        self,
        adapter: RedisStreamsAdapter,
        *,
        group: str,
        consumer: str,
        handler: EventHandler,
        retry_limit: int = _RETRY_LIMIT,
    ) -> None:
        self.adapter = adapter
        self.group = group
        self.consumer = consumer
        self.handler = handler
        self.retry_limit = retry_limit
        self._attempt_counts: dict[str, int] = {}

    def ensure_group(self) -> None:
        self.adapter.ensure_group(self.group)

    def poll_once(self, count: int = 10, block_ms: int = 100) -> int:
        """Read and process one batch. Returns number processed."""
        messages = self.adapter.xreadgroup(
            self.group, self.consumer, count=count, block_ms=block_ms
        )
        if not messages:
            return 0
        processed = 0
        for msg_id, fields in messages:
            self._handle_message(msg_id, fields)
            processed += 1
        return processed

    def _handle_message(self, msg_id: str, fields: dict[str, str]) -> None:
        attempts = self._attempt_counts.get(msg_id, 0) + 1
        self._attempt_counts[msg_id] = attempts

        try:
            event = CloudEvent.from_wire(fields)
        except Exception as exc:
            log.error("consumer.parse_failed msg_id=%s: %s", msg_id, exc)
            self.adapter.xack(self.group, msg_id)
            self._attempt_counts.pop(msg_id, None)
            return

        db = SessionLocal()
        try:
            # Idempotency check
            already = ensure_idempotent(
                db,
                event.id,
                event.type,
                consumer=f"{self.group}:{self.consumer}",
                file_id=str(event.data.get("file_id") or "") or None,
                version_no=_safe_int(event.data.get("version_no")),
                trace_id=event.trace_id,
                payload=event.to_dict(),
            )
            if already:
                log.debug("consumer.duplicate_skipped event_id=%s", event.id)
                db.commit()
                self.adapter.xack(self.group, msg_id)
                self._attempt_counts.pop(msg_id, None)
                return

            self.handler(event, db)
            db.commit()
            self.adapter.xack(self.group, msg_id)
            self._attempt_counts.pop(msg_id, None)
            log.debug("consumer.processed event_id=%s type=%s", event.id, event.type)

        except Exception as exc:
            db.rollback()
            log.warning(
                "consumer.handler_failed msg_id=%s event_id=%s attempt=%d: %s",
                msg_id, event.id, attempts, exc,
            )
            if attempts >= self.retry_limit:
                # Route to DLQ
                backoff = _RETRY_BACKOFF_SECONDS[-1]
                try:
                    data_raw = fields.get("data", "{}")
                    payload = json.loads(data_raw) if isinstance(data_raw, str) else {}
                except Exception:
                    payload = {}
                send_to_dlq(
                    db=db,
                    event_id=event.id,
                    event_type=event.type,
                    payload=payload,
                    failure_reason=str(exc),
                    retry_count=attempts,
                    redis_adapter=self.adapter,
                )
                db.commit()
                self.adapter.xack(self.group, msg_id)
                self._attempt_counts.pop(msg_id, None)
                log.error(
                    "consumer.dlq_routed event_id=%s after %d attempts",
                    event.id, attempts,
                )
            else:
                backoff = _RETRY_BACKOFF_SECONDS[min(attempts - 1, len(_RETRY_BACKOFF_SECONDS) - 1)]
                time.sleep(backoff)
        finally:
            db.close()
