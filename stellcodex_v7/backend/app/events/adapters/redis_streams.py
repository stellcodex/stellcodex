"""Redis Streams adapter — canonical event transport layer.

Uses XADD / XREADGROUP / XACK. No custom retry logic — tenacity-style
backoff is implemented in consumers.py. This module owns the wire format only.
"""
from __future__ import annotations

import json
import logging
from typing import Any, Iterator

from redis import Redis, ResponseError

log = logging.getLogger(__name__)

_MAX_STREAM_LEN = 50_000  # approximate MAXLEN trim


class RedisStreamsAdapter:
    """Thin wrapper around Redis Streams primitives."""

    def __init__(self, redis: Redis, stream_key: str) -> None:
        self.redis = redis
        self.stream_key = stream_key

    # ── publish ──────────────────────────────────────────────────────────────

    def xadd(self, fields: dict[str, str]) -> str:
        msg_id = self.redis.xadd(
            self.stream_key,
            fields,
            maxlen=_MAX_STREAM_LEN,
            approximate=True,
        )
        return str(msg_id)

    # ── consumer group ────────────────────────────────────────────────────────

    def ensure_group(self, group: str, start_id: str = "0") -> None:
        try:
            self.redis.xgroup_create(self.stream_key, group, start_id, mkstream=True)
        except ResponseError as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    def xreadgroup(
        self,
        group: str,
        consumer: str,
        count: int = 10,
        block_ms: int = 2000,
        pending: bool = False,
    ) -> list[tuple[str, dict[str, str]]]:
        """Read new (>) or pending (0) messages from group."""
        start = "0" if pending else ">"
        raw = self.redis.xreadgroup(
            group,
            consumer,
            {self.stream_key: start},
            count=count,
            block=block_ms,
        )
        if not raw:
            return []
        results: list[tuple[str, dict[str, str]]] = []
        for _stream, messages in raw:
            for msg_id, fields in messages:
                results.append((str(msg_id), {k: v for k, v in fields.items()}))
        return results

    def xack(self, group: str, *msg_ids: str) -> int:
        if not msg_ids:
            return 0
        return int(self.redis.xack(self.stream_key, group, *msg_ids))

    def xpending_count(self, group: str) -> int:
        try:
            info = self.redis.xpending(self.stream_key, group)
            return int(info.get("pending", 0)) if isinstance(info, dict) else 0
        except Exception:
            return 0

    # ── dead letter ───────────────────────────────────────────────────────────

    def xadd_dlq(self, dlq_stream: str, fields: dict[str, str]) -> str:
        msg_id = self.redis.xadd(dlq_stream, fields, maxlen=10_000, approximate=True)
        return str(msg_id)

    # ── info ──────────────────────────────────────────────────────────────────

    def xlen(self) -> int:
        try:
            return int(self.redis.xlen(self.stream_key))
        except Exception:
            return 0
