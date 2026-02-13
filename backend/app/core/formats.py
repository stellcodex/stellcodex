from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Iterable


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
    path = _formats_path()
    if not path.exists():
        raise FileNotFoundError(f"Formats allow-list missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def allowed_extensions() -> list[str]:
    data = load_formats()
    exts: list[str] = []
    for key in ("brep", "mesh", "dxf", "images"):
        exts.extend([str(x).lower() for x in data.get(key, [])])
    return sorted(set(exts))


def rejected_extensions() -> list[str]:
    data = load_formats()
    return sorted({str(x).lower() for x in data.get("rejected", [])})


def is_allowed_filename(filename: str) -> bool:
    name = (filename or "").lower()
    for ext in allowed_extensions():
        if name.endswith(f".{ext}"):
            return True
    return False


def categorize_extension(ext: str) -> str | None:
    ext = (ext or "").lower().lstrip(".")
    data = load_formats()
    for key in ("brep", "mesh", "dxf", "images"):
        if ext in [str(x).lower() for x in data.get(key, [])]:
            return key
    return None
