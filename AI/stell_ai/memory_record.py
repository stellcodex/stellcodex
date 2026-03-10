from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MemoryRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_id: str
    record_type: str
    title: str
    source_uri: str
    hash_sha256: str
    tenant_id: str
    project_id: str
    security_class: str
    time_start: str
    time_end: str
    tags: list[str] = Field(default_factory=list)
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
