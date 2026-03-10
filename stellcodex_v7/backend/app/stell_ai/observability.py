"""Structured observability — span-based tracing using stdlib logging.

Implements OpenTelemetry-compatible trace context (trace_id, span_id).
Designed to be swapped for real opentelemetry-sdk if package is installed.
"""
from __future__ import annotations

import logging
import time
import uuid
from contextlib import contextmanager
from typing import Any, Generator


log = logging.getLogger("stellcodex.otel")


class Span:
    def __init__(self, name: str, trace_id: str, parent_span_id: str | None = None) -> None:
        self.name = name
        self.trace_id = trace_id
        self.span_id = uuid.uuid4().hex[:16]
        self.parent_span_id = parent_span_id
        self._start = time.monotonic()
        self.attributes: dict[str, Any] = {}
        self.events: list[dict[str, Any]] = []

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = value

    def add_event(self, name: str, attributes: dict[str, Any] | None = None) -> None:
        self.events.append({"name": name, "attributes": attributes or {}})

    def end(self) -> None:
        duration_ms = (time.monotonic() - self._start) * 1000
        log.info(
            "span name=%s trace_id=%s span_id=%s parent=%s duration_ms=%.1f attrs=%s",
            self.name,
            self.trace_id,
            self.span_id,
            self.parent_span_id or "root",
            duration_ms,
            self.attributes,
        )


class Tracer:
    def __init__(self, trace_id: str | None = None) -> None:
        self.trace_id = trace_id or uuid.uuid4().hex
        self._active_span: Span | None = None

    @contextmanager
    def start_span(self, name: str) -> Generator[Span, None, None]:
        parent_id = self._active_span.span_id if self._active_span else None
        span = Span(name, self.trace_id, parent_id)
        prev = self._active_span
        self._active_span = span
        try:
            yield span
        finally:
            span.end()
            self._active_span = prev


def get_tracer(trace_id: str | None = None) -> Tracer:
    return Tracer(trace_id)
