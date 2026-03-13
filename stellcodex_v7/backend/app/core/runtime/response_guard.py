from __future__ import annotations

import json
import re
from typing import Any

from app.core.identity.stell_identity import RESPONSE_BLOCKED_TEXT
from app.stellai.types import now_iso

_FORBIDDEN_VALUE_PATTERNS = (
    re.compile(r"\bcodex\b", re.IGNORECASE),
    re.compile(r"\bgpt\b", re.IGNORECASE),
    re.compile(r"\bai assistant\b", re.IGNORECASE),
    re.compile(r"\bgeneric assistant\b", re.IGNORECASE),
    re.compile(r"\bassistant\b", re.IGNORECASE),
    re.compile(r"\bstorage_key\b", re.IGNORECASE),
    re.compile(r"\bobject_key\b", re.IGNORECASE),
    re.compile(r"\bbucket\b", re.IGNORECASE),
    re.compile(r"\brevision_id\b", re.IGNORECASE),
    re.compile(r"s3://", re.IGNORECASE),
    re.compile(r"r2://", re.IGNORECASE),
    re.compile(r"/root/", re.IGNORECASE),
    re.compile(r"\b(?:localhost|127\.0\.0\.1|172\.17\.0\.1)\b", re.IGNORECASE),
    re.compile(r"\btraceback\b", re.IGNORECASE),
    re.compile(r"\b[A-Za-z_]+(?:Error|Exception)\b"),
    re.compile(r"/api/[a-z0-9/_-]+", re.IGNORECASE),
)
_FORBIDDEN_KEYS = {
    "storage_key",
    "object_key",
    "bucket",
    "revision_id",
}
_REDACTED_KEYS = {
    "path",
    "tenant_root",
    "memory_path",
    "enabled_tools",
    "tenant_safe_roots",
}


def contains_forbidden_content(value: Any) -> bool:
    if isinstance(value, dict):
        return any(
            str(key).strip().lower() in _FORBIDDEN_KEYS or contains_forbidden_content(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(contains_forbidden_content(item) for item in value)
    if isinstance(value, str):
        text = str(value or "")
        return any(pattern.search(text) for pattern in _FORBIDDEN_VALUE_PATTERNS)
    return False


def _sanitize_text(value: str) -> str:
    text = str(value or "")
    return "[redacted]" if contains_forbidden_content(text) else text


def guard_text(value: str) -> str:
    return RESPONSE_BLOCKED_TEXT if contains_forbidden_content(value) else str(value or "")


def guard_text_or_default(value: str, default: str = RESPONSE_BLOCKED_TEXT) -> str:
    text = str(value or "").strip()
    if not text:
        return default
    return guard_text(text)


def guard_user_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        sanitized: dict[str, Any] = {}
        for raw_key, value in payload.items():
            key = str(raw_key)
            lowered = key.strip().lower()
            if lowered in _FORBIDDEN_KEYS:
                continue
            if lowered in _REDACTED_KEYS:
                sanitized[key] = "[redacted]"
                continue
            sanitized[key] = guard_user_payload(value)
        return sanitized
    if isinstance(payload, list):
        return [guard_user_payload(item) for item in payload]
    if isinstance(payload, str):
        return _sanitize_text(payload)
    return payload


def build_safe_runtime_payload(
    *,
    session_id: str,
    trace_id: str,
    message: str,
    reply: str,
    issue: str,
    mode: str | None = None,
) -> dict[str, Any]:
    safe_reply = guard_text_or_default(reply)
    payload = {
        "session_id": str(session_id),
        "trace_id": str(trace_id),
        "reply": safe_reply,
        "plan": {
            "graph_id": "tg_safe",
            "nodes": [],
            "metadata": {
                "safe_failure": True,
                "reason": str(issue or "safe_failure"),
                "mode": str(mode or ""),
            },
        },
        "retrieval": {
            "query": str(message or ""),
            "embedding_dim": 0,
            "filtered_out": 0,
            "used_sources": [],
            "chunks": [],
        },
        "tool_results": [],
        "memory": {
            "session": [],
            "working": [],
            "long_term": [],
        },
        "evaluation": {
            "status": "needs_attention",
            "confidence": 0.0,
            "retry_recommended": False,
            "revised": False,
            "issues": [str(issue or "safe_failure")],
            "actions": ["fail_closed"],
        },
        "events": [
            {
                "event_type": "safe_failure",
                "agent": "runtime",
                "payload": {
                    "reason": str(issue or "safe_failure"),
                    "mode": str(mode or ""),
                },
                "at": now_iso(),
            }
        ],
    }
    sanitized = guard_user_payload(payload)
    if contains_forbidden_content(sanitized):
        return {
            **payload,
            "reply": RESPONSE_BLOCKED_TEXT,
            "plan": {
                "graph_id": "tg_blocked",
                "nodes": [],
                "metadata": {"safe_failure": True, "reason": "response_guard_blocked", "mode": str(mode or "")},
            },
            "evaluation": {
                "status": "needs_attention",
                "confidence": 0.0,
                "retry_recommended": False,
                "revised": False,
                "issues": ["response_guard_blocked"],
                "actions": ["fail_closed"],
            },
            "events": [
                {
                    "event_type": "safe_failure",
                    "agent": "response_guard",
                    "payload": {"reason": "response_guard_blocked", "mode": str(mode or "")},
                    "at": now_iso(),
                }
            ],
        }
    return sanitized


def dump_guard_scan(payload: Any) -> dict[str, Any]:
    sanitized = guard_user_payload(payload)
    return {
        "forbidden_detected": contains_forbidden_content(payload),
        "forbidden_remaining": contains_forbidden_content(sanitized),
        "sanitized_preview": json.loads(json.dumps(sanitized, ensure_ascii=False, default=str)),
    }
