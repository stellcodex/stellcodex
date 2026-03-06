from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class HybridV1Config:
    materials: tuple[str, ...] = ("ABS", "PP", "PC", "PA6")
    draft_min_deg: float | None = None
    wall_mm_min: float | None = None
    wall_mm_max: float | None = None
    runner_mode_default: str = "cold"
    hot_runner: str = "needs_approval"


HYBRID_V1_CONFIG = HybridV1Config()


def get_hybrid_v1_config() -> HybridV1Config:
    return HYBRID_V1_CONFIG


def hybrid_v1_config_dict() -> dict[str, Any]:
    cfg = asdict(HYBRID_V1_CONFIG)
    cfg["materials"] = list(HYBRID_V1_CONFIG.materials)
    return cfg
