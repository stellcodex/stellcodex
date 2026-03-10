"""Deterministic geometry metrics contract for engineering analysis.

This module is the shared entry point for normalized geometry payloads used by
the runtime, persistence layer, and downstream rule engines. Keep this file in
English and update it whenever the geometry artifact schema changes.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


MODE_BREP = "BREP"
MODE_MESH_APPROX = "MESH_APPROX"
MODE_VISUAL_ONLY = "VISUAL_ONLY"

_MODE_MAP = {
    "brep": MODE_BREP,
    "mesh_approx": MODE_MESH_APPROX,
    "visual_only": MODE_VISUAL_ONLY,
    MODE_BREP.lower(): MODE_BREP,
    MODE_MESH_APPROX.lower(): MODE_MESH_APPROX,
    MODE_VISUAL_ONLY.lower(): MODE_VISUAL_ONLY,
}


def normalize_geometry_mode(value: str | None) -> str:
    token = str(value or "").strip().lower()
    return _MODE_MAP.get(token, MODE_VISUAL_ONLY)


def build_geometry_hash(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def bbox_size_vector(bbox: dict[str, Any] | None) -> list[float]:
    if not isinstance(bbox, dict):
        return []
    size = bbox.get("size")
    if isinstance(size, (list, tuple)) and len(size) >= 3:
        values = size[:3]
    elif all(key in bbox for key in ("x", "y", "z")):
        values = [bbox.get("x"), bbox.get("y"), bbox.get("z")]
    else:
        return []

    numbers: list[float] = []
    for item in values:
        try:
            numbers.append(abs(float(item)))
        except (TypeError, ValueError):
            return []
    return numbers


def infer_wall_thickness_stats(
    *,
    bbox: dict[str, Any] | None,
    mode: str,
    feature_flags: dict[str, Any] | None = None,
) -> dict[str, Any]:
    size = bbox_size_vector(bbox)
    if len(size) < 3:
        return {}

    positives = [value for value in size if value > 0]
    if not positives:
        return {}

    min_axis = min(positives)
    max_axis = max(positives)
    thinness_ratio = round(min_axis / max_axis, 6) if max_axis > 0 else 0.0
    flags = feature_flags if isinstance(feature_flags, dict) else {}
    return {
        "status": "proxy",
        "mode": normalize_geometry_mode(mode),
        "min_axis_mm": round(min_axis, 6),
        "max_axis_mm": round(max_axis, 6),
        "thinness_ratio": thinness_ratio,
        "likely_thin_wall": bool(thinness_ratio < 0.08),
        "signal_source": "bounding_box_proxy",
        "face_count_hint": flags.get("face_count"),
    }


def build_geometry_metrics_payload(
    *,
    file_id: str,
    mode: str,
    units: str = "mm",
    bbox: dict[str, Any] | None = None,
    volume: float | None = None,
    surface_area: float | None = None,
    part_count: int | None = None,
    triangle_count: int | None = None,
    source_type: str,
    confidence: float,
    wall_thickness_stats: dict[str, Any] | None = None,
    mass_estimate: float | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "file_id": str(file_id),
        "mode": normalize_geometry_mode(mode),
        "units": str(units or "mm"),
        "bbox": bbox if isinstance(bbox, dict) else {},
        "volume": volume,
        "surface_area": surface_area,
        "part_count": part_count,
        "triangle_count": triangle_count,
        "source_type": str(source_type or ""),
        "confidence": round(float(confidence), 4),
        "wall_thickness_stats": wall_thickness_stats if isinstance(wall_thickness_stats, dict) else {},
        "mass_estimate": mass_estimate,
        "metadata": metadata if isinstance(metadata, dict) else {},
    }
    payload["geometry_hash"] = build_geometry_hash(payload)
    return payload


def build_runtime_geometry_metrics(
    *,
    file_id: str,
    mode: str,
    source_type: str,
    confidence: float,
    bbox: dict[str, Any] | None = None,
    volume: float | None = None,
    surface_area: float | None = None,
    part_count: int | None = None,
    triangle_count: int | None = None,
    units: str = "mm",
    feature_flags: dict[str, Any] | None = None,
    wall_thickness_stats: dict[str, Any] | None = None,
    mass_estimate: float | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_wall_stats = wall_thickness_stats if isinstance(wall_thickness_stats, dict) and wall_thickness_stats else infer_wall_thickness_stats(
        bbox=bbox,
        mode=mode,
        feature_flags=feature_flags,
    )
    return build_geometry_metrics_payload(
        file_id=file_id,
        mode=mode,
        units=units,
        bbox=bbox,
        volume=volume,
        surface_area=surface_area,
        part_count=part_count,
        triangle_count=triangle_count,
        source_type=source_type,
        confidence=confidence,
        wall_thickness_stats=resolved_wall_stats,
        mass_estimate=mass_estimate,
        metadata=metadata,
    )
