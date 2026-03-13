from __future__ import annotations

import json

from app.core.identity.stell_identity import PLANNER_UNAVAILABLE_TEXT, RUNTIME_UNAVAILABLE_TEXT, STELL_IDENTITY_FULL
from app.stellai.channel_runtime import execute_channel_runtime
from app.stellai.runtime import StellAIRuntime
from app.stellai.types import RuntimeContext, RuntimeRequest


class _BrokenPlanner:
    def plan(self, *, request, memory):
        raise RuntimeError("CodexPlannerError: /root/secret")


class _BrokenRuntime:
    def run(self, *, request, db=None):
        raise RuntimeError("GPTBridgeError: /root/runtime")


def _context(*, file_ids: tuple[str, ...] = ()) -> RuntimeContext:
    return RuntimeContext(
        tenant_id="tenant-1",
        project_id="proj-1",
        principal_type="guest",
        principal_id="guest-1",
        session_id="sess-1",
        trace_id="trace-1",
        file_ids=file_ids,
        allowed_tools=frozenset(),
    )


def _assert_no_forbidden_tokens(payload: object) -> None:
    text = json.dumps(payload, ensure_ascii=False, default=str)
    assert "Codex" not in text
    assert "GPT" not in text
    assert "assistant" not in text.lower()
    assert "/root/" not in text


def test_identity_prompt_is_locked_to_stell_ai() -> None:
    request = RuntimeRequest(message="Sen kimsin?", context=_context(), top_k=2)
    outcome = execute_channel_runtime(request=request, db=None, runtime=_BrokenRuntime(), channel="whatsapp")

    assert outcome.reply == STELL_IDENTITY_FULL
    _assert_no_forbidden_tokens(outcome.payload)


def test_planner_failure_stays_stell_branded_and_sanitized() -> None:
    runtime = StellAIRuntime(planner=_BrokenPlanner())
    request = RuntimeRequest(message="Lutfen uretim risklerini acikla", context=_context(), top_k=2)

    outcome = execute_channel_runtime(request=request, db=None, runtime=runtime, channel="api")

    assert outcome.reply == PLANNER_UNAVAILABLE_TEXT
    _assert_no_forbidden_tokens(outcome.payload)


def test_runtime_unavailable_stays_stell_branded_and_sanitized() -> None:
    request = RuntimeRequest(message="Lutfen uretim risklerini acikla", context=_context(), top_k=2)

    outcome = execute_channel_runtime(request=request, db=None, runtime=_BrokenRuntime(), channel="api")

    assert outcome.reply == RUNTIME_UNAVAILABLE_TEXT
    _assert_no_forbidden_tokens(outcome.payload)
