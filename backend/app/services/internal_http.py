from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import HTTPException


def _normalize_base_url(value: str) -> str:
    return str(value or "").strip().rstrip("/")


def _build_url(base_url: str, path: str, query: dict[str, Any] | None = None) -> str:
    normalized_path = f"/{str(path or '').lstrip('/')}"
    url = f"{_normalize_base_url(base_url)}{normalized_path}"
    if query:
        encoded = urlencode(
            [(str(key), "" if value is None else str(value)) for key, value in query.items() if value is not None],
            doseq=True,
        )
        if encoded:
            url = f"{url}?{encoded}"
    return url


def _decode_json(raw: bytes | None) -> Any:
    if not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return {"detail": raw.decode("utf-8", errors="ignore").strip() or "Upstream returned an unreadable response"}


def request_json(
    *,
    base_url: str,
    path: str,
    method: str = "GET",
    query: dict[str, Any] | None = None,
    payload: dict[str, Any] | list[Any] | None = None,
    timeout: int = 10,
) -> Any:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(
        _build_url(base_url, path, query=query),
        data=data,
        headers=headers,
        method=method.upper(),
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            return _decode_json(response.read())
    except HTTPError as exc:
        payload = _decode_json(exc.read())
        detail = payload.get("detail") if isinstance(payload, dict) else payload
        raise HTTPException(status_code=exc.code, detail=detail or "Upstream service rejected the request")
    except URLError as exc:
        raise HTTPException(status_code=503, detail=f"Internal service unavailable: {exc.reason}")

