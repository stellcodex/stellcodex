from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


TRUTH_ROOT = Path(os.getenv("PHASE2_TRUTH_ROOT", "/root/workspace/_truth"))
MEMORY_DIR = TRUTH_ROOT / "records" / "memory"


@dataclass
class MemoryRecord:
    record_id: str
    record_type: str
    title: str
    source_uri: str
    hash_sha256: str
    tenant_id: str
    project_id: str
    tags: list[str]
    text: str
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "record_type": self.record_type,
            "title": self.title,
            "source_uri": self.source_uri,
            "hash_sha256": self.hash_sha256,
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "tags": self.tags,
            "text": self.text,
            "metadata": self.metadata,
        }


def _stable_hash(text: str, metadata: dict[str, Any]) -> str:
    payload = json.dumps({"text": text, "metadata": metadata}, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_memory_record(
    *,
    record_type: str,
    title: str,
    source_uri: str,
    tenant_id: str,
    project_id: str,
    tags: list[str] | None = None,
    text: str,
    metadata: dict[str, Any] | None = None,
    record_id: str | None = None,
) -> MemoryRecord:
    clean_metadata = metadata if isinstance(metadata, dict) else {}
    rid = record_id or f"mem_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}_{uuid4().hex[:10]}"
    return MemoryRecord(
        record_id=rid,
        record_type=str(record_type),
        title=str(title),
        source_uri=str(source_uri),
        hash_sha256=_stable_hash(text, clean_metadata),
        tenant_id=str(tenant_id or "0"),
        project_id=str(project_id or "default"),
        tags=[str(tag) for tag in (tags or []) if str(tag).strip()],
        text=str(text),
        metadata=clean_metadata,
    )


def write_memory_record(record: MemoryRecord) -> Path:
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    path = MEMORY_DIR / f"{record.record_id}.json"
    path.write_text(json.dumps(record.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def write_memory_payload(
    *,
    record_type: str,
    title: str,
    source_uri: str,
    tenant_id: str,
    project_id: str,
    tags: list[str] | None,
    text: str,
    metadata: dict[str, Any] | None,
) -> Path:
    record = build_memory_record(
        record_type=record_type,
        title=title,
        source_uri=source_uri,
        tenant_id=tenant_id,
        project_id=project_id,
        tags=tags,
        text=text,
        metadata=metadata,
    )
    return write_memory_record(record)
