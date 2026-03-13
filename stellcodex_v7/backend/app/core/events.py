from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


_SPEC_VERSION = "1.0"
_DEFAULT_CONTENT_TYPE = "application/json"
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
    specversion: str = _SPEC_VERSION
    datacontenttype: str = _DEFAULT_CONTENT_TYPE
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "specversion": self.specversion,
            "id": self.id,
            "type": self.type,
            "source": self.source,
            "subject": self.subject,
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "trace_id": self.trace_id,
            "time": self.time,
            "datacontenttype": self.datacontenttype,
            "data": self.data,
        }

    def to_wire(self) -> dict[str, str]:
        payload = self.to_dict()
        return {
            "specversion": self.specversion,
            "id": self.id,
            "source": self.source,
            "type": self.type,
            "subject": self.subject,
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "trace_id": self.trace_id,
            "time": self.time,
            "datacontenttype": self.datacontenttype,
            "data": json.dumps(self.data, ensure_ascii=False, separators=(",", ":")),
            "payload": json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
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
            specversion=_SPEC_VERSION,
            id=event_id or str(uuid4()),
            type=str(event_type),
            source=str(source),
            subject=str(subject),
            tenant_id=str(tenant_id or "0"),
            project_id=str(project_id or "default"),
            trace_id=str(trace_id or uuid4()),
            time=timestamp or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            datacontenttype=_DEFAULT_CONTENT_TYPE,
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
            specversion=str(payload.get("specversion") or _SPEC_VERSION),
            id=str(payload["id"]),
            type=str(payload["type"]),
            source=str(payload["source"]),
            subject=str(payload["subject"]),
            tenant_id=str(payload["tenant_id"]),
            project_id=str(payload["project_id"]),
            trace_id=str(payload["trace_id"]),
            time=str(payload["time"]),
            datacontenttype=str(payload.get("datacontenttype") or _DEFAULT_CONTENT_TYPE),
            data=data,
        )

    @classmethod
    def from_wire(cls, fields: dict[str, Any]) -> "EventEnvelope":
        payload_raw = fields.get("payload")
        if isinstance(payload_raw, str) and payload_raw.strip():
            try:
                decoded = json.loads(payload_raw)
                if isinstance(decoded, dict):
                    return cls.from_dict(decoded)
            except Exception:
                pass

        data_raw = fields.get("data", "{}")
        if isinstance(data_raw, dict):
            data = data_raw
        elif isinstance(data_raw, str):
            try:
                decoded = json.loads(data_raw)
                data = decoded if isinstance(decoded, dict) else {}
            except Exception:
                data = {}
        else:
            data = {}

        return cls(
            specversion=str(fields.get("specversion") or _SPEC_VERSION),
            id=str(fields.get("id") or uuid4()),
            type=str(fields.get("type") or "unknown"),
            source=str(fields.get("source") or "unknown"),
            subject=str(fields.get("subject") or ""),
            tenant_id=str(fields.get("tenant_id") or ""),
            project_id=str(fields.get("project_id") or ""),
            trace_id=str(fields.get("trace_id") or uuid4()),
            time=str(fields.get("time") or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
            datacontenttype=str(fields.get("datacontenttype") or _DEFAULT_CONTENT_TYPE),
            data=data,
        )
