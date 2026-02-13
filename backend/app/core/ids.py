from __future__ import annotations

import re
from uuid import uuid4, UUID

SCX_ID_PREFIX = "scx_"
SCX_ID_PATTERN = re.compile(r"^scx_[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")


def generate_scx_id() -> str:
    return f"{SCX_ID_PREFIX}{uuid4()}"


def is_scx_id(value: str) -> bool:
    return bool(SCX_ID_PATTERN.match(value or ""))


def normalize_scx_id(value: str) -> str:
    raw = (value or "").strip()
    if raw.startswith(SCX_ID_PREFIX) and is_scx_id(raw):
        return raw
    try:
        uid = UUID(raw)
    except Exception:
        raise ValueError("Invalid SCX id")
    return f"{SCX_ID_PREFIX}{uid}"
