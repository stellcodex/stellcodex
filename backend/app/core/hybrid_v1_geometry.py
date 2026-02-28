from __future__ import annotations

from pathlib import Path
import os
from typing import Any, Mapping
UNKNOWN = "unknown"
STEP_EXTENSIONS = {"step", "stp"}
CRITICAL_GEOMETRY_FIELDS = ("draft_deg_min", "wall_mm_min", "has_undercut", "complexity_risk")
STEP_COMPLEXITY_KEYWORDS = ("ADVANCED_FACE", "EDGE_LOOP", "CLOSED_SHELL")

# Deterministic score thresholds:
# - LOW: score < 300
# - MED: 300 <= score < 2000
# - HIGH: score >= 2000
COMPLEXITY_LOW_MAX = 300
COMPLEXITY_MED_MAX = 2000


def _is_unknown(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"", "unknown", "none", "null", "n/a", "na"}
    return False


def _complexity_label_from_score(score: int) -> str:
    if score < COMPLEXITY_LOW_MAX:
        return "LOW"
    if score < COMPLEXITY_MED_MAX:
        return "MED"
    return "HIGH"


def step_text_complexity(step_path: str | Path) -> dict[str, int]:
    path = Path(step_path)
    text = path.read_text(encoding="utf-8", errors="ignore")
    size_bytes = path.stat().st_size
    line_count = text.count("\n") + (0 if text.endswith("\n") else 1 if text else 0)
    normalized = text.upper()
    entity_count_heuristic = sum(normalized.count(keyword) for keyword in STEP_COMPLEXITY_KEYWORDS)
    complexity_risk_score = (entity_count_heuristic * 2) + (line_count // 40) + (size_bytes // 50000)

    return {
        "line_count": line_count,
        "entity_count_heuristic": entity_count_heuristic,
        "size_bytes": size_bytes,
        "complexity_risk_score": complexity_risk_score,
    }


def build_geometry_report_for_step(step_path: str | Path, provided_inputs: Mapping[str, Any] | None = None) -> dict[str, Any]:
    path = Path(step_path)
    if not path.exists():
        raise FileNotFoundError(f"STEP file not found: {path}")
    if not path.is_file():
        raise ValueError(f"STEP path is not a file: {path}")

    ext = path.suffix.lower().lstrip(".")
    if ext not in STEP_EXTENSIONS:
        raise ValueError(f"Expected STEP extension, got: {path.suffix}")

    geometry: dict[str, Any] = {
        "units": UNKNOWN,
        "part_count": UNKNOWN,
        "draft_deg_min": UNKNOWN,
        "wall_mm_min": UNKNOWN,
        "wall_mm_max": UNKNOWN,
        "has_undercut": UNKNOWN,
        "complexity_risk": UNKNOWN,
    }

    # --- Real geometry extraction (step_extractor) ---
    extracted: dict[str, Any] = {}
    try:
        from app.services.step_extractor import extract_step_geometry
        result = extract_step_geometry(path)
        extracted = result.to_geometry_meta()

        geometry["units"] = result.units
        geometry["part_count"] = result.part_count

        # Surface-based wall thickness heuristic:
        # If we have a bounding box, the smallest dimension is a proxy for min wall.
        if result.bbox:
            dims = sorted([result.bbox.x, result.bbox.y, result.bbox.z])
            geometry["wall_mm_min"] = round(dims[0], 4)
            geometry["wall_mm_max"] = round(dims[2], 4)

        geometry["complexity_risk"] = result.complexity.label
        geometry["has_undercut"] = UNKNOWN   # requires true B-rep kernel; left for future
        geometry["draft_deg_min"] = UNKNOWN  # requires surface normal analysis; left for future

    except Exception:
        # Fall back to the original text-complexity heuristic
        complexity_metrics: dict[str, int] | None = None
        try:
            complexity_metrics = step_text_complexity(path)
        except OSError:
            complexity_metrics = None
        if complexity_metrics is not None:
            score = int(complexity_metrics["complexity_risk_score"])
            geometry["complexity_risk"] = _complexity_label_from_score(score)

    complexity_metrics: dict[str, int] | None = None
    try:
        complexity_metrics = step_text_complexity(path)
    except OSError:
        complexity_metrics = None
    if complexity_metrics is not None and geometry["complexity_risk"] == UNKNOWN:
        score = int(complexity_metrics["complexity_risk_score"])
        geometry["complexity_risk"] = _complexity_label_from_score(score)

    # provided_inputs policy
    # PROD default: only fill UNKNOWN fields
    # DEMO/admin override (if HYBRID_V1_OVERRIDE_PROVIDED=1)
    override = os.environ.get("HYBRID_V1_OVERRIDE_PROVIDED", "").strip() == "1"
    if provided_inputs:
        for k in CRITICAL_GEOMETRY_FIELDS:
            if k not in provided_inputs:
                continue
            v = provided_inputs.get(k)
            if _is_unknown(v):
                continue
            if override:
                geometry[k] = v
            else:
                if _is_unknown(geometry.get(k)):
                    geometry[k] = v

    # recompute unknowns afterwards

    critical_unknowns = [name for name in CRITICAL_GEOMETRY_FIELDS if _is_unknown(geometry.get(name))]

    return {
        "schema": "hybrid_v1.geometry_report",
        "source": {
            "step_path": str(path),
            "filename": path.name,
            "ext": ext,
            "size_bytes": path.stat().st_size,
        },
        "geometry": geometry,
        "complexity_metrics": complexity_metrics,
        "critical_unknowns": critical_unknowns,
        "parser": {"name": "hybrid_v1_step_parser", "status": "partial", "unknowns_allowed": True},
    }
