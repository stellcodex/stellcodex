"""Design intent interpretation from deterministic geometry evidence."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _feature_summary(feature_map: dict[str, Any], name: str) -> dict[str, Any]:
    return _as_dict(_as_dict(feature_map).get("features")).get(name) if isinstance(_as_dict(_as_dict(feature_map).get("features")).get(name), dict) else {}


def build_design_intent(
    *,
    file_id: str,
    geometry_metrics: dict[str, Any] | None,
    feature_map: dict[str, Any] | None,
    assembly_structure: dict[str, Any] | None = None,
    knowledge_refs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    metrics = _as_dict(geometry_metrics)
    features = _as_dict(feature_map)
    bbox = _as_dict(metrics.get("bbox"))
    size = bbox.get("size") if isinstance(bbox.get("size"), list) else []
    holes = _feature_summary(features, "holes")
    threads = _feature_summary(features, "threads")
    drafts = _feature_summary(features, "drafts")
    thin_walls = _feature_summary(features, "thin_walls")

    functional_features: list[dict[str, Any]] = []
    if holes:
        functional_features.append({"name": "holes", "count": holes.get("count"), "signal": holes.get("detection_mode")})
    if threads:
        functional_features.append({"name": "threads", "count": threads.get("count"), "signal": threads.get("detection_mode")})
    if not functional_features:
        functional_features.append({"name": "external_form", "count": 1, "signal": "baseline_geometry"})

    structural_features: list[dict[str, Any]] = []
    part_count = _as_int(metrics.get("part_count"), 1) or 1
    structural_features.append({"name": "part_count", "value": part_count})
    if thin_walls:
        structural_features.append({"name": "thin_wall_proxy", "count": thin_walls.get("count"), "signal": thin_walls.get("detection_mode")})
    if drafts:
        structural_features.append({"name": "draft_signal", "count": drafts.get("count"), "signal": drafts.get("detection_mode")})
    if assembly_structure:
        structural_features.append(
            {
                "name": "assembly_structure",
                "occurrence_count": _as_int(assembly_structure.get("occurrence_count"), part_count),
                "mode": assembly_structure.get("mode"),
            }
        )

    manufacturing_sensitive_features: list[dict[str, Any]] = []
    if thin_walls:
        manufacturing_sensitive_features.append(
            {
                "name": "thin_walls",
                "severity": "medium",
                "reason": "Thin wall proxy raises manufacturability sensitivity.",
            }
        )
    if threads:
        manufacturing_sensitive_features.append(
            {
                "name": "threads",
                "severity": "medium",
                "reason": "Threaded details often add secondary operations or tooling complexity.",
            }
        )
    if not manufacturing_sensitive_features and part_count > 1:
        manufacturing_sensitive_features.append(
            {
                "name": "multi_part_coordination",
                "severity": "low",
                "reason": "Multiple parts increase assembly handling and inspection scope.",
            }
        )

    critical_dimensions = {
        "bbox_size_mm": size if len(size) >= 3 else None,
        "max_span_mm": max(size) if size else None,
        "min_span_mm": min(size) if size else None,
        "volume_mm3": metrics.get("volume"),
        "part_count": part_count,
    }
    return {
        "schema": "stellcodex.v10.design_intent",
        "generated_at": _now_iso(),
        "file_id": str(file_id),
        "geometry_hash": str(metrics.get("geometry_hash") or ""),
        "functional_features": functional_features,
        "structural_features": structural_features,
        "critical_dimensions": critical_dimensions,
        "manufacturing_sensitive_features": manufacturing_sensitive_features,
        "knowledge_refs": list(knowledge_refs or []),
    }
