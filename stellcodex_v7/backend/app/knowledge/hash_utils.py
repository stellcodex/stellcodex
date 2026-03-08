from __future__ import annotations

import hashlib
import json
from typing import Any


def stable_hash_text(text: str) -> str:
    return hashlib.sha256(str(text or "").encode("utf-8")).hexdigest()


def stable_hash_json(payload: dict[str, Any]) -> str:
    data = json.dumps(payload if isinstance(payload, dict) else {}, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def stable_hash_payload(*, text: str, metadata: dict[str, Any]) -> str:
    return stable_hash_json({"text": str(text or ""), "metadata": metadata if isinstance(metadata, dict) else {}})


def make_chunk_hash(record_id: str, chunk_index: int, text: str) -> str:
    return stable_hash_text(f"{record_id}|{int(chunk_index)}|{text}")


def make_id(prefix: str, *parts: Any, size: int = 32) -> str:
    material = "|".join(str(item) for item in parts)
    digest = stable_hash_text(material)
    return f"{prefix}_{digest[: max(8, int(size))]}"
