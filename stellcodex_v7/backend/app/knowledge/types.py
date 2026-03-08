from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


INDEX_STATUS_PENDING = "pending"
INDEX_STATUS_INDEXED = "indexed"
INDEX_STATUS_SKIPPED = "skipped"
INDEX_STATUS_FAILED = "failed"

FAILURE_SOURCE_NOT_FOUND = "SOURCE_NOT_FOUND"
FAILURE_NORMALIZATION_FAIL = "NORMALIZATION_FAIL"
FAILURE_EMBEDDING_FAIL = "EMBEDDING_FAIL"
FAILURE_INDEX_WRITE_FAIL = "INDEX_WRITE_FAIL"
FAILURE_TENANT_SCOPE_FAIL = "TENANT_SCOPE_FAIL"
FAILURE_INVALID_PAYLOAD = "INVALID_PAYLOAD"

INDEX_VERSION_DEFAULT = "v1"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class CanonicalKnowledgeRecord:
    record_id: str
    tenant_id: str
    project_id: str | None
    file_id: str | None
    source_type: str
    source_subtype: str
    source_ref: str
    title: str
    text: str
    summary: str
    metadata: dict[str, Any]
    tags: list[str]
    security_class: str
    hash_sha256: str
    index_version: str
    embedding_status: str = INDEX_STATUS_PENDING
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "file_id": self.file_id,
            "source_type": self.source_type,
            "source_subtype": self.source_subtype,
            "source_ref": self.source_ref,
            "title": self.title,
            "text": self.text,
            "summary": self.summary,
            "metadata": self.metadata,
            "tags": self.tags,
            "security_class": self.security_class,
            "hash_sha256": self.hash_sha256,
            "index_version": self.index_version,
            "embedding_status": self.embedding_status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
