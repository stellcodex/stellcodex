from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel, Field, ValidationError


class RenderPreset(BaseModel):
    name: str
    label: str | None = None
    engine: str | None = None


class RenderPresetSpec(BaseModel):
    presets: list[RenderPreset] = Field(default_factory=list)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _presets_path() -> Path:
    return _repo_root() / "backend" / "app" / "data" / "render-presets.json"


def load_render_presets() -> RenderPresetSpec:
    path = _presets_path()
    if not path.exists():
        raise FileNotFoundError(f"Render preset spec missing: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    try:
        return RenderPresetSpec.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"Invalid render preset spec: {exc}")


@lru_cache(maxsize=1)
def get_render_presets() -> RenderPresetSpec:
    return load_render_presets()


def list_render_presets() -> Iterable[RenderPreset]:
    return get_render_presets().presets


def get_render_preset(name: str) -> RenderPreset:
    for preset in list_render_presets():
        if preset.name == name:
            return preset
    raise KeyError(f"Unknown render preset: {name}")
