from __future__ import annotations

"""Channel-facing runtime wrapper.

This layer preserves multilingual keyword detection while keeping the
implementation notes and default system messages English-first.
"""

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from app.core.identity.stell_identity import (
    ENGINEERING_ASYNC_ACCEPTED_TEXT,
    GENERAL_FAILURE_TEXT,
    RUNTIME_UNAVAILABLE_TEXT,
    STELL_IDENTITY_FULL,
    STELL_IDENTITY_NAME,
    stell_identity,
)
from app.core.runtime.message_mode import MessageMode, detect_mode, is_identity_prompt
from app.core.runtime.response_guard import (
    build_safe_runtime_payload,
    contains_forbidden_content,
    guard_text_or_default,
    guard_user_payload,
)
from app.stellai.runtime import StellAIRuntime
from app.stellai.types import RuntimeRequest


@dataclass(frozen=True)
class ChannelRuntimeOutcome:
    mode: MessageMode
    reply: str
    payload: dict[str, Any]
    job_id: str | None = None


def execute_channel_runtime(
    *,
    request: RuntimeRequest,
    db: Session | None,
    runtime: StellAIRuntime | None = None,
    channel: str,
) -> ChannelRuntimeOutcome:
    mode = detect_mode(request.message)
    if is_identity_prompt(request.message):
        payload = build_safe_runtime_payload(
            session_id=request.context.session_id,
            trace_id=request.context.trace_id,
            message=request.message,
            reply=stell_identity(),
            issue="identity_locked",
            mode=mode.value,
        )
        return ChannelRuntimeOutcome(mode=mode, reply=payload["reply"], payload=payload)

    if mode is MessageMode.SYSTEM_STATUS:
        reply = f"{STELL_IDENTITY_NAME} runtime status is ready."
        payload = build_safe_runtime_payload(
            session_id=request.context.session_id,
            trace_id=request.context.trace_id,
            message=request.message,
            reply=reply,
            issue="system_status",
            mode=mode.value,
        )
        payload["evaluation"]["status"] = "pass"
        payload["evaluation"]["confidence"] = 1.0
        payload["evaluation"]["issues"] = []
        payload["evaluation"]["actions"] = ["system_status_formatted"]
        return ChannelRuntimeOutcome(mode=mode, reply=reply, payload=payload)

    if mode is MessageMode.GENERAL_CHAT and channel in {"admin", "whatsapp"} and not request.context.file_ids:
        reply = (
            f"{STELL_IDENTITY_FULL}. "
            "I handle engineering analysis, file status, and system status workflows."
        )
        payload = build_safe_runtime_payload(
            session_id=request.context.session_id,
            trace_id=request.context.trace_id,
            message=request.message,
            reply=reply,
            issue="scope_reply",
            mode=mode.value,
        )
        payload["evaluation"]["status"] = "pass"
        payload["evaluation"]["confidence"] = 0.8
        payload["evaluation"]["issues"] = []
        payload["evaluation"]["actions"] = ["scope_reply"]
        return ChannelRuntimeOutcome(mode=mode, reply=payload["reply"], payload=payload)

    if _should_dispatch_engineering_async(request=request, mode=mode, channel=channel):
        try:
            from app.workers.tasks import enqueue_engineering_analysis

            job_id = enqueue_engineering_analysis(request.context.file_ids[0])
            payload = build_safe_runtime_payload(
                session_id=request.context.session_id,
                trace_id=request.context.trace_id,
                message=request.message,
                reply=ENGINEERING_ASYNC_ACCEPTED_TEXT,
                issue="engineering_async_dispatched",
                mode=mode.value,
            )
            payload["plan"]["metadata"]["job_id"] = job_id
            payload["evaluation"]["status"] = "pass"
            payload["evaluation"]["confidence"] = 0.92
            payload["evaluation"]["issues"] = []
            payload["evaluation"]["actions"] = ["engineering_async_dispatched"]
            payload["events"][0]["payload"]["job_id"] = job_id
            return ChannelRuntimeOutcome(
                mode=mode,
                reply=ENGINEERING_ASYNC_ACCEPTED_TEXT,
                payload=payload,
                job_id=job_id,
            )
        except Exception:
            payload = build_safe_runtime_payload(
                session_id=request.context.session_id,
                trace_id=request.context.trace_id,
                message=request.message,
                reply=GENERAL_FAILURE_TEXT,
                issue="engineering_queue_unavailable",
                mode=mode.value,
            )
            return ChannelRuntimeOutcome(mode=mode, reply=payload["reply"], payload=payload)

    try:
        runtime = runtime or StellAIRuntime()
        result = runtime.run(request=request, db=db)
        payload = result.to_dict()
        payload.setdefault("plan", {}).setdefault("metadata", {})["mode"] = mode.value
        payload = guard_user_payload(payload)
        reply = guard_text_or_default(str(payload.get("reply") or ""), default=RUNTIME_UNAVAILABLE_TEXT)
        payload["reply"] = reply
        if contains_forbidden_content(payload):
            payload = build_safe_runtime_payload(
                session_id=request.context.session_id,
                trace_id=request.context.trace_id,
                message=request.message,
                reply=GENERAL_FAILURE_TEXT,
                issue="response_guard_blocked",
                mode=mode.value,
            )
            reply = payload["reply"]
        return ChannelRuntimeOutcome(mode=mode, reply=reply, payload=payload)
    except Exception:
        payload = build_safe_runtime_payload(
            session_id=request.context.session_id,
            trace_id=request.context.trace_id,
            message=request.message,
            reply=RUNTIME_UNAVAILABLE_TEXT,
            issue="runtime_unavailable",
            mode=mode.value,
        )
        return ChannelRuntimeOutcome(mode=mode, reply=payload["reply"], payload=payload)


def _should_dispatch_engineering_async(*, request: RuntimeRequest, mode: MessageMode, channel: str) -> bool:
    if channel != "whatsapp":
        return False
    if mode is not MessageMode.ENGINEERING:
        return False
    if not request.context.file_ids:
        return False
    lowered = str(request.message or "").lower()
    heavy_tokens = (
        "analyze",
        "analysis",
        "dfm",
        "feature",
        "volume",
        "surface",
        "mesh",
        "geometry",
        "analiz",
        "hacim",
        "yüzey",
        "yuzey",
        "özellik",
        "ozellik",
    )
    return any(token in lowered for token in heavy_tokens)
