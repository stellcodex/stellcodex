"""V10 engineering master report assembly."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def build_engineering_master_report(
    *,
    file_id: str,
    geometry_metrics: dict[str, Any] | None,
    feature_map: dict[str, Any] | None,
    manufacturing_decision: dict[str, Any] | None,
    manufacturing_plan: dict[str, Any] | None,
    cost_estimate: dict[str, Any] | None,
    dfm_report: dict[str, Any] | None,
    design_intent: dict[str, Any] | None,
    process_simulation: dict[str, Any] | None,
    cost_optimization: dict[str, Any] | None,
    design_optimization: dict[str, Any] | None,
    engineering_decision: dict[str, Any] | None,
    knowledge_refs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    geometry_payload = _as_dict(geometry_metrics)
    feature_payload = _as_dict(feature_map)
    decision_payload = _as_dict(manufacturing_decision)
    plan_payload = _as_dict(manufacturing_plan)
    cost_payload = _as_dict(cost_estimate)
    dfm_payload = _as_dict(dfm_report)
    design_intent_payload = _as_dict(design_intent)
    simulation_payload = _as_dict(process_simulation)
    cost_optimization_payload = _as_dict(cost_optimization)
    design_optimization_payload = _as_dict(design_optimization)
    engineering_decision_payload = _as_dict(engineering_decision)

    report = {
        "schema": "stellcodex.v10.engineering_master_report",
        "generated_at": _now_iso(),
        "file_id": str(file_id),
        "geometry_summary": geometry_payload,
        "feature_summary": feature_payload,
        "design_intent": design_intent_payload,
        "manufacturing_prediction": decision_payload,
        "manufacturing_recommendation": decision_payload,
        "manufacturing_plan": plan_payload,
        "process_simulation": simulation_payload,
        "cost_estimate": cost_payload,
        "cost_analysis": {
            "cost_estimate": cost_payload,
            "cost_optimization": cost_optimization_payload,
        },
        "dfm_report": {
            "report_hash": dfm_payload.get("report_hash"),
            "recommended_changes": dfm_payload.get("recommended_changes"),
            "conflict_flags": dfm_payload.get("conflict_flags"),
            "risk_count": len(dfm_payload.get("risks") or []),
            "risks": dfm_payload.get("risks"),
        },
        "design_optimization": design_optimization_payload,
        "engineering_decision": engineering_decision_payload,
        "design_improvements": list(dfm_payload.get("recommended_changes") or []),
        "design_recommendations": engineering_decision_payload.get("design_recommendations") or [],
        "knowledge_refs": list(knowledge_refs or []),
        "capability_status": str(
            decision_payload.get("capability_status")
            or cost_payload.get("capability_status")
            or plan_payload.get("capability_status")
            or "degraded"
        ),
    }
    report["report_hash"] = hashlib.sha256(
        json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    ).hexdigest()
    return report
