"""Deterministic cost optimization layer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def build_cost_optimization(
    *,
    file_id: str,
    cost_estimate: dict[str, Any] | None,
    manufacturing_plan: dict[str, Any] | None,
    process_simulation: dict[str, Any] | None,
) -> dict[str, Any]:
    estimate = _as_dict(cost_estimate)
    plan = _as_dict(manufacturing_plan)
    simulation = _as_dict(process_simulation)
    baseline_cost = _as_float(estimate.get("estimated_batch_cost"))
    if baseline_cost <= 0.0:
        baseline_cost = _as_float(estimate.get("estimated_unit_cost"))
    setup_count = max(1, _as_int(plan.get("setup_count"), 1))
    tool_accessibility = str(simulation.get("tool_accessibility") or "good")
    setup_complexity = str(simulation.get("setup_complexity") or "low")
    process = str(plan.get("recommended_process") or estimate.get("recommended_process") or "unknown")

    savings_factor = 0.0
    optimization_suggestions: list[str] = []
    if setup_count > 1:
        savings_factor += 0.08
        optimization_suggestions.append("Reduce setup count by consolidating orientations or fixtures.")
    if tool_accessibility in {"limited", "poor"}:
        savings_factor += 0.04
        optimization_suggestions.append("Open tool access around constrained regions to reduce secondary operations.")
    if setup_complexity == "high":
        savings_factor += 0.03
        optimization_suggestions.append("Stabilize datum strategy to lower fixture churn.")
    if process == "injection_molding" and baseline_cost > 0.0:
        savings_factor += 0.05
        optimization_suggestions.append("Validate tooling amortization against expected production volume.")
    if process == "3d_printing":
        optimization_suggestions.append("Group low-volume builds to improve machine utilization.")

    savings_factor = min(0.22, round(savings_factor, 4))
    optimized_cost = round(max(0.0, baseline_cost * (1.0 - savings_factor)), 2)
    return {
        "schema": "stellcodex.v10.cost_optimization",
        "generated_at": _now_iso(),
        "file_id": str(file_id),
        "baseline_cost": round(baseline_cost, 2),
        "optimized_cost": optimized_cost,
        "cost_drivers": list(estimate.get("cost_drivers") or []),
        "optimization_suggestions": optimization_suggestions,
        "currency": str(estimate.get("currency") or "EUR"),
        "savings_factor": savings_factor,
        "savings_value": round(max(0.0, baseline_cost - optimized_cost), 2),
    }
