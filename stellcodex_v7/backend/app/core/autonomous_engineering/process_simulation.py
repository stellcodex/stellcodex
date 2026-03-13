"""Deterministic manufacturing process simulation."""

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


def build_process_simulation(
    *,
    file_id: str,
    geometry_metrics: dict[str, Any] | None,
    feature_map: dict[str, Any] | None,
    manufacturing_plan: dict[str, Any] | None,
) -> dict[str, Any]:
    metrics = _as_dict(geometry_metrics)
    features = _as_dict(_as_dict(feature_map).get("features"))
    plan = _as_dict(manufacturing_plan)
    process = str(plan.get("recommended_process") or "unknown")
    holes = _as_int(_as_dict(features.get("holes")).get("count"))
    threads = _as_int(_as_dict(features.get("threads")).get("count"))
    thin_walls = _as_int(_as_dict(features.get("thin_walls")).get("count"))
    setup_count = max(1, _as_int(plan.get("setup_count"), 1))
    part_count = max(1, _as_int(metrics.get("part_count"), 1))

    feasibility_score = 0.86
    risk_flags: list[dict[str, Any]] = []
    notes: list[str] = []

    if thin_walls > 0:
        feasibility_score -= 0.14
        risk_flags.append({"code": "thin_wall_sensitivity", "severity": "medium"})
        notes.append("Thin wall proxy reduces confidence in stable process execution.")
    if threads > 0 and process == "injection_molding":
        feasibility_score -= 0.16
        risk_flags.append({"code": "thread_tooling_complexity", "severity": "high"})
        notes.append("Threaded geometry increases tooling complexity for molding.")
    if setup_count > 1:
        feasibility_score -= 0.08
        risk_flags.append({"code": "multi_setup_flow", "severity": "medium"})
        notes.append("Multiple setups raise fixture and handoff complexity.")
    if part_count > 1:
        feasibility_score -= 0.05
        notes.append("Assembly-level handling expands inspection scope.")
    if holes > 10:
        feasibility_score -= 0.05
        notes.append("High hole count increases feature-level toolpath complexity.")

    feasibility_score = max(0.0, round(feasibility_score, 4))
    machining_feasibility = "feasible" if feasibility_score >= 0.72 else "review_required"
    collision_risk = "high" if any(item["severity"] == "high" for item in risk_flags) else "medium" if risk_flags else "low"
    tool_accessibility = "poor" if setup_count >= 3 else "limited" if setup_count == 2 or holes > 8 else "good"
    setup_complexity = "high" if setup_count >= 3 else "medium" if setup_count == 2 else "low"

    return {
        "schema": "stellcodex.v10.process_simulation",
        "generated_at": _now_iso(),
        "file_id": str(file_id),
        "geometry_hash": str(metrics.get("geometry_hash") or ""),
        "recommended_process": process,
        "machining_feasibility": machining_feasibility,
        "collision_risk": collision_risk,
        "tool_accessibility": tool_accessibility,
        "setup_complexity": setup_complexity,
        "feasibility_score": feasibility_score,
        "risk_flags": risk_flags,
        "notes": notes,
    }
