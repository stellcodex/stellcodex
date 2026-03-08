from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


REQUIRED_EVENT_KEYS = (
    "id",
    "type",
    "source",
    "subject",
    "tenant_id",
    "project_id",
    "trace_id",
    "time",
    "data",
)


@dataclass(frozen=True)
class EventEnvelope:
    id: str
    type: str
    source: str
    subject: str
    tenant_id: str
    project_id: str
    trace_id: str
    time: str
    data: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "source": self.source,
            "subject": self.subject,
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "trace_id": self.trace_id,
            "time": self.time,
            "data": self.data,
        }

    @classmethod
    def build(
        cls,
        *,
        event_type: str,
        source: str,
        subject: str,
        tenant_id: str,
        project_id: str,
        data: dict[str, Any] | None = None,
        trace_id: str | None = None,
        event_id: str | None = None,
        timestamp: str | None = None,
    ) -> "EventEnvelope":
        return cls(
            id=event_id or str(uuid4()),
            type=str(event_type),
            source=str(source),
            subject=str(subject),
            tenant_id=str(tenant_id or "0"),
            project_id=str(project_id or "default"),
            trace_id=str(trace_id or uuid4()),
            time=timestamp or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            data=data if isinstance(data, dict) else {},
        )

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EventEnvelope":
        missing = [key for key in REQUIRED_EVENT_KEYS if key not in payload]
        if missing:
            raise ValueError(f"event envelope missing keys: {missing}")
        data = payload.get("data")
        if not isinstance(data, dict):
            raise ValueError("event envelope field 'data' must be object")
        return cls(
            id=str(payload["id"]),
            type=str(payload["type"]),
            source=str(payload["source"]),
            subject=str(payload["subject"]),
            tenant_id=str(payload["tenant_id"]),
            project_id=str(payload["project_id"]),
            trace_id=str(payload["trace_id"]),
            time=str(payload["time"]),
            data=data,
        )
