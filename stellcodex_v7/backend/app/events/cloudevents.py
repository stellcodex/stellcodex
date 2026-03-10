"""CloudEvents v1.0 schema helpers.

Only the fields required by STELLCODEX are enforced.
Spec: https://cloudevents.io/
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


_SPEC_VERSION = "1.0"


class CloudEvent(BaseModel):
    """Canonical CloudEvent envelope used across the event spine."""

    specversion: str = Field(default=_SPEC_VERSION)
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str
    type: str
    subject: str
    tenant_id: str
    project_id: str
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    time: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    datacontenttype: str = Field(default="application/json")
    data: dict[str, Any] = Field(default_factory=dict)

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
    ) -> "CloudEvent":
        return cls(
            id=event_id or str(uuid.uuid4()),
            type=event_type,
            source=source,
            subject=subject,
            tenant_id=str(tenant_id),
            project_id=str(project_id),
            trace_id=trace_id or str(uuid.uuid4()),
            data=data or {},
        )

    def to_wire(self) -> dict[str, str]:
        """Flatten to Redis Streams wire format (all strings)."""
        import json
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
            "data": json.dumps(self.data, ensure_ascii=False, separators=(",", ":")),
        }

    @classmethod
    def from_wire(cls, fields: dict[str, str]) -> "CloudEvent":
        import json
        data_raw = fields.get("data", "{}")
        try:
            data = json.loads(data_raw) if isinstance(data_raw, str) else {}
        except Exception:
            data = {}
        return cls(
            specversion=fields.get("specversion", _SPEC_VERSION),
            id=fields.get("id", str(uuid.uuid4())),
            source=fields.get("source", "unknown"),
            type=fields.get("type", "unknown"),
            subject=fields.get("subject", ""),
            tenant_id=fields.get("tenant_id", ""),
            project_id=fields.get("project_id", ""),
            trace_id=fields.get("trace_id", str(uuid.uuid4())),
            time=fields.get("time", datetime.now(timezone.utc).isoformat()),
            data=data,
        )
