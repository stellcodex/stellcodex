"""Deterministic feature extraction baseline for supported geometry modes.

The runtime intentionally fails closed for unsupported feature families. Extend
this file only when a feature can be backed by deterministic evidence.
"""

from __future__ import annotations

from typing import Any

from app.core.engineering.geometry_metrics import MODE_BREP, MODE_MESH_APPROX, MODE_VISUAL_ONLY, normalize_geometry_mode


FEATURE_EXTRACTOR_VERSION = "engineering_features.v2"


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _feature_entry(
    *,
    supported: bool,
    count: int | None,
    confidence: float,
    detection_mode: str,
    notes: str,
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "supported": bool(supported),
        "count": count,
        "confidence": round(float(confidence), 4),
        "detection_mode": str(detection_mode),
        "evidence_refs": list(evidence_refs or []),
        "notes": str(notes or ""),
    }


def build_feature_map(
    *,
    mode: str,
    geometry_metrics: dict[str, Any] | None = None,
    feature_flags: dict[str, Any] | None = None,
    source_signals: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_mode = normalize_geometry_mode(mode)
    metrics = _as_dict(geometry_metrics)
    flags = _as_dict(feature_flags)
    signals = _as_dict(source_signals)
    wall_stats = _as_dict(metrics.get("wall_thickness_stats"))
    surface_breakdown = _as_dict(flags.get("surface_breakdown") or signals.get("surface_breakdown"))
    thread_hints = signals.get("thread_hints")
    if not isinstance(thread_hints, list):
        thread_hints = ["thread_hint"] if bool(flags.get("thread_hints")) else []

    unsupported_note = "geometry fidelity does not support deterministic detection in this runtime"
    feature_map = {
        "extractor_version": FEATURE_EXTRACTOR_VERSION,
        "mode": normalized_mode,
        "features": {},
    }
    features = feature_map["features"]

    hole_count = _as_int(flags.get("hole_count"))
    features["holes"] = _feature_entry(
        supported=normalized_mode == MODE_BREP and hole_count is not None,
        count=hole_count if normalized_mode == MODE_BREP and hole_count is not None else None,
        confidence=0.88 if normalized_mode == MODE_BREP and hole_count is not None else 0.0,
        detection_mode="step_entity_resolution" if normalized_mode == MODE_BREP and hole_count is not None else "unsupported",
        notes="derived from deterministic hole extraction" if normalized_mode == MODE_BREP and hole_count is not None else unsupported_note,
        evidence_refs=["feature_flags.hole_count"] if hole_count is not None else [],
    )

    thread_count = len(thread_hints)
    features["threads"] = _feature_entry(
        supported=normalized_mode == MODE_BREP,
        count=thread_count if normalized_mode == MODE_BREP else None,
        confidence=0.66 if normalized_mode == MODE_BREP and thread_count else 0.18 if normalized_mode == MODE_BREP else 0.0,
        detection_mode="step_entity_hint" if normalized_mode == MODE_BREP else "unsupported",
        notes="derived from STEP thread hints" if normalized_mode == MODE_BREP and thread_count else unsupported_note,
        evidence_refs=["source_signals.thread_hints"] if thread_count else [],
    )

    conical_count = _as_int(surface_breakdown.get("conical"))
    draft_supported = normalized_mode == MODE_BREP and conical_count is not None
    features["drafts"] = _feature_entry(
        supported=draft_supported,
        count=conical_count if draft_supported else None,
        confidence=0.41 if draft_supported and conical_count else 0.15 if draft_supported else 0.0,
        detection_mode="surface_proxy" if draft_supported else "unsupported",
        notes="derived from conical surface count; not an exact draft-angle measurement" if draft_supported else unsupported_note,
        evidence_refs=["feature_flags.surface_breakdown.conical"] if draft_supported else [],
    )

    thin_ratio = wall_stats.get("thinness_ratio")
    likely_thin_wall = bool(wall_stats.get("likely_thin_wall"))
    thin_supported = normalized_mode in {MODE_BREP, MODE_MESH_APPROX} and thin_ratio is not None
    features["thin_walls"] = _feature_entry(
        supported=thin_supported,
        count=1 if thin_supported and likely_thin_wall else 0 if thin_supported else None,
        confidence=0.49 if thin_supported and likely_thin_wall else 0.27 if thin_supported else 0.0,
        detection_mode="bounding_box_proxy" if thin_supported else "unsupported",
        notes="derived from bounding-box thinness proxy; not a sectional wall-thickness solve" if thin_supported else unsupported_note,
        evidence_refs=["geometry_metrics.wall_thickness_stats.thinness_ratio"] if thin_supported else [],
    )

    for name in ("slots", "pockets", "ribs", "fillets", "chamfers", "undercuts", "bosses"):
        features[name] = _feature_entry(
            supported=False,
            count=None,
            confidence=0.0,
            detection_mode="unsupported",
            notes=unsupported_note if normalized_mode != MODE_VISUAL_ONLY else "visual-only path cannot support deterministic extraction",
        )

    return feature_map
