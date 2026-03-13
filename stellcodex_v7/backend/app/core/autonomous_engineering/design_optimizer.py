"""Deterministic manufacturability-focused design optimization."""

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


def build_design_optimization(
    *,
    file_id: str,
    feature_map: dict[str, Any] | None,
    manufacturing_decision: dict[str, Any] | None,
    process_simulation: dict[str, Any] | None,
) -> dict[str, Any]:
    features = _as_dict(_as_dict(feature_map).get("features"))
    decision = _as_dict(manufacturing_decision)
    simulation = _as_dict(process_simulation)
    suggestions: list[dict[str, Any]] = []

    thin_walls = _as_int(_as_dict(features.get("thin_walls")).get("count"))
    threads = _as_int(_as_dict(features.get("threads")).get("count"))
    drafts = _as_int(_as_dict(features.get("drafts")).get("count"))
    process = str(decision.get("recommended_process") or "unknown")

    if thin_walls > 0:
        suggestions.append(
            {
                "id": "stabilize_thin_sections",
                "title": "Stabilize thin sections",
                "category": "wall_thickness",
                "impact": "high",
                "reason": "Thin wall proxy increases manufacturing sensitivity and deformation risk.",
                "recommended_action": "Increase wall support or normalize local thickness transitions.",
            }
        )
    if threads > 0:
        suggestions.append(
            {
                "id": "simplify_threads",
                "title": "Simplify threaded details",
                "category": "feature_complexity",
                "impact": "medium",
                "reason": "Threaded features raise tooling or secondary operation load.",
                "recommended_action": "Move threads to post-machining or standard inserts where possible.",
            }
        )
    if process == "injection_molding" and drafts <= 0:
        suggestions.append(
            {
                "id": "increase_draft_angle",
                "title": "Increase draft angle",
                "category": "release",
                "impact": "high",
                "reason": "Molding flow without draft raises release risk.",
                "recommended_action": "Add draft to molded faces before tooling commitment.",
            }
        )
    if str(simulation.get("tool_accessibility") or "good") in {"limited", "poor"}:
        suggestions.append(
            {
                "id": "open_tool_access",
                "title": "Open tool access",
                "category": "accessibility",
                "impact": "medium",
                "reason": "Restricted access increases setup and collision risk.",
                "recommended_action": "Simplify deep or narrow regions to reduce tool reach constraints.",
            }
        )

    manufacturability_gain = round(min(0.35, len(suggestions) * 0.07), 4)
    return {
        "schema": "stellcodex.v10.design_optimization",
        "generated_at": _now_iso(),
        "file_id": str(file_id),
        "status": "actionable" if suggestions else "no_changes_required",
        "suggestions": suggestions,
        "priority_actions": [item["title"] for item in suggestions[:3]],
        "manufacturability_gain": manufacturability_gain,
    }
