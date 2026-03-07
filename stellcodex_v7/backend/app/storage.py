from __future__ import annotations

import os
from pathlib import Path

from .config import settings


class Storage:
    def __init__(self, root: str | None = None) -> None:
        base = root or getattr(settings, "workdir", None) or settings.storage_root
        self.root = Path(base)

    def ensure_dir(self, key: str) -> Path:
        path = self.root / key
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def write_bytes(self, key: str, data: bytes) -> str:
        path = self.ensure_dir(key)
        path.write_bytes(data)
        return key

    def copy_from(self, src: Path, key: str) -> str:
        path = self.ensure_dir(key)
        path.write_bytes(src.read_bytes())
        return key

    def exists(self, key: str) -> bool:
        return (self.root / key).exists()


def storage_key_for_3d(project_id: str, revision_id: str, filename: str) -> str:
    return f"models/{project_id}/{revision_id}/{filename}"


def storage_key_for_2d(project_id: str, revision_id: str, filename: str) -> str:
    return f"drawings/{project_id}/{revision_id}/{filename}"


def storage_key_for_render(project_id: str, revision_id: str, filename: str) -> str:
    return f"renders/{project_id}/{revision_id}/{filename}"
