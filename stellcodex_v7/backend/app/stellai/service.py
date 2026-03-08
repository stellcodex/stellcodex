from __future__ import annotations

from functools import lru_cache

from app.stellai.runtime import StellAIRuntime


@lru_cache(maxsize=1)
def get_stellai_runtime() -> StellAIRuntime:
    return StellAIRuntime()
