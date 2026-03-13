from __future__ import annotations

import asyncio
import hashlib
import hmac
import json

from fastapi import HTTPException

from app.api.v1.routes import whatsapp as whatsapp_route
from app.core.runtime.message_mode import MessageMode
from app.stellai.channel_runtime import ChannelRuntimeOutcome


class _FakeRequest:
    def __init__(self, payload: dict, headers: dict[str, str] | None = None) -> None:
        self._body = json.dumps(payload).encode("utf-8")
        self.headers = headers or {}

    async def body(self) -> bytes:
        return self._body


def test_whatsapp_verify_webhook_accepts_matching_token(monkeypatch) -> None:
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "wa-local-token")

    response = whatsapp_route.verify_whatsapp_webhook(
        mode="subscribe",
        verify_token="wa-local-token",
        challenge="12345",
    )

    assert response == "12345"


def test_whatsapp_verify_webhook_rejects_mismatched_token(monkeypatch) -> None:
    monkeypatch.setenv("WHATSAPP_VERIFY_TOKEN", "wa-local-token")

    try:
        whatsapp_route.verify_whatsapp_webhook(
            mode="subscribe",
            verify_token="wrong-token",
            challenge="12345",
        )
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("verify endpoint should reject mismatched token")


def test_whatsapp_route_binds_to_stell_runtime(monkeypatch) -> None:
    observed: dict[str, object] = {}

    def fake_scope(*, db, sender: str, requested_file_ids: tuple[str, ...]):
        observed["scope_sender"] = sender
        observed["scope_file_ids"] = requested_file_ids
        return "tenant-42", requested_file_ids

    def fake_runtime():
        observed["runtime_requested"] = True
        return object()

    def fake_execute_channel_runtime(*, request, db, runtime, channel: str):
        observed["channel"] = channel
        observed["message"] = request.message
        observed["principal_type"] = request.context.principal_type
        observed["principal_id"] = request.context.principal_id
        return ChannelRuntimeOutcome(
            mode=MessageMode.GENERAL_CHAT,
            reply="STELL-AI — Stellcodex Engineering Intelligence",
            payload={
                "session_id": request.context.session_id,
                "trace_id": request.context.trace_id,
                "reply": "STELL-AI — Stellcodex Engineering Intelligence",
                "plan": {"graph_id": "tg_safe", "nodes": [], "metadata": {}},
                "retrieval": {"query": request.message, "embedding_dim": 0, "filtered_out": 0, "used_sources": [], "chunks": []},
                "tool_results": [],
                "memory": {"session": [], "working": [], "long_term": []},
                "evaluation": {"status": "pass", "confidence": 1.0, "retry_recommended": False, "revised": False, "issues": [], "actions": []},
                "events": [],
            },
        )

    monkeypatch.setattr(whatsapp_route, "_resolve_whatsapp_scope", fake_scope)
    monkeypatch.setattr(whatsapp_route, "get_stellai_runtime", fake_runtime)
    monkeypatch.setattr(whatsapp_route, "execute_channel_runtime", fake_execute_channel_runtime)

    response = asyncio.run(
        whatsapp_route.whatsapp_webhook(
            _FakeRequest({"sender": "+90 555 111 22 33", "message": "Sen kimsin?"}),
            db=object(),
        )
    )

    assert response.status == "ok"
    assert response.reply.startswith("STELL-AI")
    assert observed["channel"] == "whatsapp"
    assert observed["message"] == "Sen kimsin?"
    assert observed["principal_type"] == "whatsapp"
    assert str(observed["principal_id"]).startswith("whatsapp:")


def test_whatsapp_route_returns_sanitized_failure_when_scope_rejects(monkeypatch) -> None:
    def fake_scope(*, db, sender: str, requested_file_ids: tuple[str, ...]):
        raise RuntimeError("CodexError /root/private")

    monkeypatch.setattr(whatsapp_route, "_resolve_whatsapp_scope", fake_scope)

    response = asyncio.run(
        whatsapp_route.whatsapp_webhook(
            _FakeRequest({"sender": "+90 555 111 22 33", "message": "status"}),
            db=object(),
        )
    )

    assert response.status == "error"
    assert response.reply.startswith("STELL-AI")


def test_whatsapp_route_rejects_invalid_signature_when_secret_is_configured(monkeypatch) -> None:
    monkeypatch.setenv("WHATSAPP_APP_SECRET", "wa-app-secret")

    try:
        asyncio.run(
            whatsapp_route.whatsapp_webhook(
                _FakeRequest({"sender": "+90 555 111 22 33", "message": "status"}),
                db=object(),
            )
        )
    except HTTPException as exc:
        assert exc.status_code == 403
    else:
        raise AssertionError("signature verification should reject unsigned webhook")


def test_whatsapp_route_accepts_valid_signature_when_secret_is_configured(monkeypatch) -> None:
    observed: dict[str, object] = {}
    monkeypatch.setenv("WHATSAPP_APP_SECRET", "wa-app-secret")

    def fake_scope(*, db, sender: str, requested_file_ids: tuple[str, ...]):
        return "tenant-42", requested_file_ids

    def fake_execute_channel_runtime(*, request, db, runtime, channel: str):
        observed["channel"] = channel
        return ChannelRuntimeOutcome(
            mode=MessageMode.GENERAL_CHAT,
            reply="ok",
            payload={"session_id": request.context.session_id, "trace_id": request.context.trace_id},
        )

    payload = {"sender": "+90 555 111 22 33", "message": "Merhaba"}
    raw = json.dumps(payload).encode("utf-8")
    signature = hmac.new(b"wa-app-secret", raw, hashlib.sha256).hexdigest()

    monkeypatch.setattr(whatsapp_route, "_resolve_whatsapp_scope", fake_scope)
    monkeypatch.setattr(whatsapp_route, "get_stellai_runtime", lambda: object())
    monkeypatch.setattr(whatsapp_route, "execute_channel_runtime", fake_execute_channel_runtime)

    response = asyncio.run(
        whatsapp_route.whatsapp_webhook(
            _FakeRequest(payload, headers={"x-hub-signature-256": f"sha256={signature}"}),
            db=object(),
        )
    )

    assert response.status == "ok"
    assert observed["channel"] == "whatsapp"
