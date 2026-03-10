"""Deterministic manufacturing process selection rules.

This module converts geometry and feature evidence into a process recommendation
without handing authority to the AI layer.
"""

from __future__ import annotations

from typing import Any

from app.core.engineering.geometry_metrics import MODE_BREP, MODE_MESH_APPROX, MODE_VISUAL_ONLY, normalize_geometry_mode


RULE_VERSION = "manufacturing_rules.v1"
KNOWN_PROCESSES = ("cnc_machining", "injection_molding", "3d_printing")


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _feature_count(feature_map: dict[str, Any], name: str) -> int | None:
    features = _as_dict(feature_map.get("features"))
    feature = _as_dict(features.get(name))
    try:
        value = feature.get("count")
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _add_rule_hit(rule_hits: list[dict[str, Any]], *, rule_id: str, process: str, score_delta: float, reason: str) -> None:
    rule_hits.append(
        {
            "rule_id": rule_id,
            "process": process,
            "score_delta": round(float(score_delta), 4),
            "reason": str(reason),
        }
    )


def build_manufacturing_decision(
    *,
    mode: str,
    geometry_metrics: dict[str, Any] | None = None,
    feature_map: dict[str, Any] | None = None,
    quantity: int | None = None,
) -> dict[str, Any]:
    normalized_mode = normalize_geometry_mode(mode)
    metrics = _as_dict(geometry_metrics)
    features = _as_dict(feature_map)
    qty = max(1, int(quantity or 1))

    if normalized_mode == MODE_VISUAL_ONLY:
        return {
            "rule_version": RULE_VERSION,
            "recommended_process": "unknown",
            "confidence": 0.0,
            "dfm_risk_score": 0.9,
            "rule_hits": [],
            "recommended_changes": ["Provide B-Rep or watertight mesh geometry before manufacturing classification."],
            "conflict_flags": ["insufficient_geometry_fidelity"],
            "capability_status": "degraded",
            "scores": {},
        }

    scores = {name: 0.0 for name in KNOWN_PROCESSES}
    rule_hits: list[dict[str, Any]] = []
    recommended_changes: list[str] = []
    conflict_flags: list[str] = []

    holes = _feature_count(features, "holes") or 0
    threads = _feature_count(features, "threads") or 0
    drafts = _feature_count(features, "drafts") or 0
    thin_walls = _feature_count(features, "thin_walls") or 0
    volume = metrics.get("volume")
    triangle_count = metrics.get("triangle_count")

    scores["cnc_machining"] += 0.2
    _add_rule_hit(
        rule_hits,
        rule_id="base_cnc",
        process="cnc_machining",
        score_delta=0.2,
        reason="Deterministic baseline for supported engineering geometry.",
    )

    if holes > 0:
        scores["cnc_machining"] += 0.3
        _add_rule_hit(
            rule_hits,
            rule_id="holes_favor_cnc",
            process="cnc_machining",
            score_delta=0.3,
            reason="Detected holes increase CNC suitability.",
        )

    if threads > 0:
        scores["cnc_machining"] += 0.2
        _add_rule_hit(
            rule_hits,
            rule_id="threads_favor_cnc",
            process="cnc_machining",
            score_delta=0.2,
            reason="Thread signals favor machining over molding.",
        )
        conflict_flags.append("threaded_features_raise_mold_complexity")
        recommended_changes.append("Separate threaded details or plan post-machining if molding is required.")

    if normalized_mode == MODE_BREP and qty >= 50:
        scores["injection_molding"] += 0.25
        _add_rule_hit(
            rule_hits,
            rule_id="brep_quantity_favors_molding",
            process="injection_molding",
            score_delta=0.25,
            reason="High quantity with B-Rep fidelity supports molding review.",
        )

    if drafts > 0:
        scores["injection_molding"] += 0.2
        _add_rule_hit(
            rule_hits,
            rule_id="draft_signal_favors_molding",
            process="injection_molding",
            score_delta=0.2,
            reason="Draft-like conical surfaces support molding suitability.",
        )

    if thin_walls > 0 and qty >= 100:
        scores["injection_molding"] += 0.2
        _add_rule_hit(
            rule_hits,
            rule_id="thin_wall_volume_favors_molding",
            process="injection_molding",
            score_delta=0.2,
            reason="Thin-wall proxy with higher quantity supports molding economics.",
        )

    if qty <= 10:
        scores["3d_printing"] += 0.2
        _add_rule_hit(
            rule_hits,
            rule_id="low_volume_favors_printing",
            process="3d_printing",
            score_delta=0.2,
            reason="Low quantity favors additive workflows.",
        )

    if normalized_mode == MODE_MESH_APPROX:
        scores["3d_printing"] += 0.2
        _add_rule_hit(
            rule_hits,
            rule_id="mesh_mode_favors_printing",
            process="3d_printing",
            score_delta=0.2,
            reason="Mesh-native path aligns naturally with additive preparation.",
        )

    if isinstance(volume, (int, float)) and float(volume) < 100000.0:
        scores["3d_printing"] += 0.15
        _add_rule_hit(
            rule_hits,
            rule_id="small_volume_favors_printing",
            process="3d_printing",
            score_delta=0.15,
            reason="Small material volume reduces additive cost risk.",
        )

    if isinstance(triangle_count, int) and triangle_count > 0 and triangle_count < 5000:
        scores["3d_printing"] += 0.05
        _add_rule_hit(
            rule_hits,
            rule_id="light_mesh_favors_printing",
            process="3d_printing",
            score_delta=0.05,
            reason="Low triangle count suggests manageable additive preparation.",
        )

    if normalized_mode == MODE_BREP and drafts == 0 and qty >= 100:
        conflict_flags.append("missing_draft_signal_for_molding")
        recommended_changes.append("Add draft angles before considering injection molding.")
        scores["injection_molding"] = max(0.0, scores["injection_molding"] - 0.1)

    if thin_walls > 0 and threads > 0:
        conflict_flags.append("thin_walls_and_threads_raise_complexity")
        recommended_changes.append("Review thread placement in thin-wall regions to reduce manufacturing risk.")

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    recommended_process, best_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0.0

    if best_score < 0.25:
        recommended_process = "unknown"
        confidence = 0.0
        conflict_flags.append("insufficient_rule_signal")
        recommended_changes.append("Collect richer feature evidence before locking manufacturing method.")
    else:
        confidence = min(0.95, round(best_score + max(0.0, best_score - second_score) * 0.3, 4))

    dfm_risk_score = min(1.0, round(0.2 + 0.15 * len(conflict_flags), 4))
    capability_status = "supported" if recommended_process != "unknown" else "degraded"

    dedup_changes: list[str] = []
    seen_changes: set[str] = set()
    for item in recommended_changes:
        token = str(item).strip()
        if not token or token in seen_changes:
            continue
        seen_changes.add(token)
        dedup_changes.append(token)

    dedup_conflicts = list(dict.fromkeys(str(item).strip() for item in conflict_flags if str(item).strip()))

    return {
        "rule_version": RULE_VERSION,
        "recommended_process": recommended_process,
        "confidence": confidence,
        "dfm_risk_score": dfm_risk_score,
        "rule_hits": rule_hits,
        "recommended_changes": dedup_changes,
        "conflict_flags": dedup_conflicts,
        "capability_status": capability_status,
        "scores": {name: round(value, 4) for name, value in scores.items()},
    }
