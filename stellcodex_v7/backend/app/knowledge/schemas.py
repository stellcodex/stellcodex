from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


SECURITY_CLASSES = ("public", "internal", "restricted", "system")


@dataclass(frozen=True)
class MemoryRecord:
    record_id: str
    record_type: str
    title: str
    source_uri: str
    hash_sha256: str
    tenant_id: str | None
    project_id: str | None
    security_class: str
    time_start: str | None
    time_end: str | None
    tags: list[str]
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not str(self.record_id or "").strip():
            raise ValueError("record_id is required")
        if not str(self.record_type or "").strip():
            raise ValueError("record_type is required")
        if not str(self.title or "").strip():
            raise ValueError("title is required")
        if not str(self.source_uri or "").strip():
            raise ValueError("source_uri is required")
        if not str(self.hash_sha256 or "").strip():
            raise ValueError("hash_sha256 is required")
        if not str(self.text or "").strip():
            raise ValueError("text cannot be empty")
        if str(self.security_class or "").strip() not in SECURITY_CLASSES:
            raise ValueError("security_class is invalid")

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "record_type": self.record_type,
            "title": self.title,
            "source_uri": self.source_uri,
            "hash_sha256": self.hash_sha256,
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "security_class": self.security_class,
            "time_start": self.time_start,
            "time_end": self.time_end,
            "tags": list(self.tags),
            "text": self.text,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ChunkRecord:
    chunk_id: str
    record_id: str
    chunk_index: int
    text: str
    token_estimate: int
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.chunk_id:
            raise ValueError("chunk_id is required")
        if not self.record_id:
            raise ValueError("record_id is required")
        if self.chunk_index < 0:
            raise ValueError("chunk_index must be >= 0")
        if not str(self.text or "").strip():
            raise ValueError("chunk text cannot be empty")
        if self.token_estimate <= 0:
            raise ValueError("token_estimate must be > 0")

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "record_id": self.record_id,
            "chunk_index": int(self.chunk_index),
            "text": self.text,
            "token_estimate": int(self.token_estimate),
            "metadata": dict(self.metadata),
        }
