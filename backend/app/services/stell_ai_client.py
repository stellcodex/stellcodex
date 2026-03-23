from __future__ import annotations

from typing import Any

from app.core.config import settings
from app.services.internal_http import request_json


def proxy_stell_ai(
    *,
    path: str,
    method: str = "GET",
    query: dict[str, Any] | None = None,
    payload: dict[str, Any] | list[Any] | None = None,
    timeout: int = 20,
) -> Any:
    return request_json(
        base_url=settings.stell_ai_base_url,
        path=path,
        method=method,
        query=query,
        payload=payload,
        timeout=timeout,
    )


def decide_with_stell_ai(
    *,
    file_id: str | None = None,
    project_id: str | None = None,
    mode: str | None = None,
    rule_version: str | None = None,
    geometry_meta: dict[str, Any] | None = None,
    dfm_findings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if file_id:
        payload["file_id"] = file_id
    if project_id:
        payload["project_id"] = project_id
    if mode:
        payload["mode"] = mode
    if rule_version:
        payload["rule_version"] = rule_version
    if isinstance(geometry_meta, dict):
        payload["geometry_meta"] = geometry_meta
    if isinstance(dfm_findings, dict):
        payload["dfm_findings"] = dfm_findings
    return proxy_stell_ai(path="/decide", method="POST", payload=payload, timeout=20)


def analyze_with_stell_ai(
    *,
    file_id: str | None = None,
    include_web_context: bool = False,
    web_query: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"include_web_context": bool(include_web_context)}
    if file_id:
        payload["file_id"] = file_id
    if web_query:
        payload["web_query"] = web_query
    return proxy_stell_ai(path="/analyze", method="POST", payload=payload, timeout=30)

