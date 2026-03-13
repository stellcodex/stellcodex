from __future__ import annotations

from typing import Any

__all__ = [
    "StellAIRuntime",
    "get_stellai_runtime",
    "execute_channel_runtime",
    "RuntimeContext",
    "RuntimeRequest",
    "RuntimeResponse",
]


def __getattr__(name: str) -> Any:
    if name == "StellAIRuntime":
        from app.stell_ai.runtime import StellAIRuntime

        return StellAIRuntime
    if name == "get_stellai_runtime":
        from app.stell_ai.runtime import get_stellai_runtime

        return get_stellai_runtime
    if name == "execute_channel_runtime":
        from app.stell_ai.runtime import execute_channel_runtime

        return execute_channel_runtime
    if name in {"RuntimeContext", "RuntimeRequest", "RuntimeResponse"}:
        from app.stell_ai.types import RuntimeContext, RuntimeRequest, RuntimeResponse

        mapping = {
            "RuntimeContext": RuntimeContext,
            "RuntimeRequest": RuntimeRequest,
            "RuntimeResponse": RuntimeResponse,
        }
        return mapping[name]
    raise AttributeError(name)
