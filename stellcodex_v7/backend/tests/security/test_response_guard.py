from __future__ import annotations

import asyncio
import json

from app.api.v1.routes.whatsapp import whatsapp_webhook
from app.core.identity.stell_identity import GENERAL_FAILURE_TEXT, RESPONSE_BLOCKED_TEXT
from app.core.runtime.response_guard import build_safe_runtime_payload, dump_guard_scan


class _FakeRequest:
    def __init__(self, payload) -> None:
        self._body = json.dumps(payload).encode("utf-8")
        self.headers: dict[str, str] = {}

    async def body(self) -> bytes:
        return self._body


def test_response_guard_strips_forbidden_identity_and_infra_leaks() -> None:
    payload = {
        "reply": "I am Codex and the bucket is s3://secret",
        "bucket": "private-bucket",
        "path": "/root/workspace/private.txt",
        "nested": {"detail": "RuntimeError on /api/v1/private"},
    }

    report = dump_guard_scan(payload)

    assert report["forbidden_detected"] is True
    assert report["forbidden_remaining"] is False
    assert report["sanitized_preview"]["reply"] == "[redacted]"
    assert "bucket" not in report["sanitized_preview"]


def test_safe_runtime_payload_blocks_forbidden_reply_text() -> None:
    payload = build_safe_runtime_payload(
        session_id="sess-1",
        trace_id="trace-1",
        message="status",
        reply="GPT RuntimeError at /root/private",
        issue="runtime_unavailable",
        mode="SYSTEM_STATUS",
    )

    assert payload["reply"] == RESPONSE_BLOCKED_TEXT


def test_whatsapp_webhook_error_body_is_sanitized() -> None:
    response = asyncio.run(whatsapp_webhook(_FakeRequest({}), db=None))

    assert response.status == "error"
    assert response.reply == GENERAL_FAILURE_TEXT
