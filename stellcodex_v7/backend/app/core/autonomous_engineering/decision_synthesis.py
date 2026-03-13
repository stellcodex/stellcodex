"""Decision synthesis across deterministic engineering artifacts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def build_engineering_decision(
    *,
    file_id: str,
    manufacturing_decision: dict[str, Any] | None,
    manufacturing_plan: dict[str, Any] | None,
    cost_estimate: dict[str, Any] | None,
    process_simulation: dict[str, Any] | None,
    design_optimization: dict[str, Any] | None,
    dfm_report: dict[str, Any] | None,
    knowledge_refs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    decision = _as_dict(manufacturing_decision)
    plan = _as_dict(manufacturing_plan)
    estimate = _as_dict(cost_estimate)
    simulation = _as_dict(process_simulation)
    optimization = _as_dict(design_optimization)
    dfm = _as_dict(dfm_report)
    risks = list(dfm.get("risks") or []) + list(simulation.get("risk_flags") or [])
    recommendations = list(dfm.get("recommended_changes") or []) + [
        str(item.get("recommended_action"))
        for item in list(optimization.get("suggestions") or [])
        if isinstance(item, dict) and str(item.get("recommended_action") or "").strip()
    ]

    return {
        "schema": "stellcodex.v10.engineering_decision",
        "generated_at": _now_iso(),
        "file_id": str(file_id),
        "recommended_process": str(decision.get("recommended_process") or plan.get("recommended_process") or "unknown"),
        "manufacturing_plan": plan,
        "cost_estimate": {
            "currency": estimate.get("currency"),
            "estimated_unit_cost": estimate.get("estimated_unit_cost"),
            "estimated_batch_cost": estimate.get("estimated_batch_cost"),
        },
        "design_risks": risks,
        "design_recommendations": recommendations,
        "confidence": decision.get("confidence"),
        "knowledge_refs": list(knowledge_refs or []),
    }
