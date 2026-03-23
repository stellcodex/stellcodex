from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.services.internal_http import request_json


def proxy_orchestra(
    *,
    path: str,
    method: str = "GET",
    query: dict[str, Any] | None = None,
    payload: dict[str, Any] | list[Any] | None = None,
    timeout: int = 15,
) -> Any:
    return request_json(
        base_url=settings.orchestra_base_url,
        path=path,
        method=method,
        query=query,
        payload=payload,
        timeout=timeout,
    )


def sync_orchestrator_file(file_id: str) -> dict[str, Any]:
    return proxy_orchestra(path="/files/sync", method="POST", payload={"file_id": file_id}, timeout=20)
