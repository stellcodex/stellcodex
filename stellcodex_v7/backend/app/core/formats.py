from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from app.core.format_registry import (
    find_mode,
    get_rule_by_ext,
    is_allowed_filename as _registry_allowed_filename,
    rejected_extensions as _registry_rejected_extensions,
    to_legacy_groups,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _formats_path() -> Path:
    here = Path(__file__).resolve()
    candidates = [
        here.parents[1] / "data" / "formats.json",  # /app/app/data/formats.json (container/runtime)
        _repo_root() / "backend" / "app" / "data" / "formats.json",  # repo checkout layout
    ]
    for path in candidates:
        if path.exists():
            return path
    return candidates[0]


@lru_cache(maxsize=1)
def load_formats() -> dict:
    # V7 single-source registry lives in format_registry.py.
    # Keep this function for backward compatibility with legacy callers.
    return to_legacy_groups()


def allowed_extensions() -> list[str]:
    data = load_formats()
    exts: list[str] = []
    for key in ("brep", "mesh", "dxf", "images"):
        exts.extend([str(x).lower() for x in data.get(key, [])])
    return sorted(set(exts))


def rejected_extensions() -> list[str]:
    return _registry_rejected_extensions()


def is_allowed_filename(filename: str) -> bool:
    return _registry_allowed_filename(filename)


def categorize_extension(ext: str) -> str | None:
    ext = (ext or "").lower().lstrip(".")
    mode = find_mode(ext)
    if mode == "brep":
        return "brep"
    if mode in {"mesh_approx", "visual_only"}:
        return "mesh"
    if mode == "2d_only":
        return "dxf"
    rule = get_rule_by_ext(ext)
    if rule and rule.kind in {"doc", "image"}:
        return "images"
    return None
