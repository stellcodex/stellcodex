from __future__ import annotations

from typing import Any

__all__ = [
    "StellAIRuntime",
    "get_stellai_runtime",
    "RuntimeContext",
    "RuntimeRequest",
    "RuntimeResponse",
]


def __getattr__(name: str) -> Any:
    if name == "StellAIRuntime":
        from app.stellai.runtime import StellAIRuntime

        return StellAIRuntime
    if name == "get_stellai_runtime":
        from app.stellai.service import get_stellai_runtime

        return get_stellai_runtime
    if name in {"RuntimeContext", "RuntimeRequest", "RuntimeResponse"}:
        from app.stellai.types import RuntimeContext, RuntimeRequest, RuntimeResponse

        mapping = {
            "RuntimeContext": RuntimeContext,
            "RuntimeRequest": RuntimeRequest,
            "RuntimeResponse": RuntimeResponse,
        }
        return mapping[name]
    raise AttributeError(name)
