"""Autonomous engineering orchestration over deterministic artifacts."""

from __future__ import annotations

from typing import Any

from app.core.autonomous_engineering.cost_optimizer import build_cost_optimization
from app.core.autonomous_engineering.decision_synthesis import build_engineering_decision
from app.core.autonomous_engineering.design_interpreter import build_design_intent
from app.core.autonomous_engineering.design_optimizer import build_design_optimization
from app.core.autonomous_engineering.knowledge_base import load_default_knowledge_base
from app.core.autonomous_engineering.manufacturing_planner import build_autonomous_manufacturing_plan
from app.core.autonomous_engineering.process_simulation import build_process_simulation
from app.core.autonomous_engineering.report_generation import build_engineering_master_report


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _feature_tags(feature_map: dict[str, Any] | None) -> list[str]:
    features = _as_dict(_as_dict(feature_map).get("features"))
    tags: list[str] = []
    for name in ("holes", "threads", "drafts", "thin_walls"):
        payload = _as_dict(features.get(name))
        if payload:
            tags.append(name)
    return tags


def _build_query(
    *,
    geometry_metrics: dict[str, Any] | None,
    manufacturing_decision: dict[str, Any] | None,
    feature_map: dict[str, Any] | None,
) -> str:
    metrics = _as_dict(geometry_metrics)
    decision = _as_dict(manufacturing_decision)
    bbox = _as_dict(metrics.get("bbox"))
    size = bbox.get("size") if isinstance(bbox.get("size"), list) else []
    return " ".join(
        [
            str(metrics.get("mode") or "unknown"),
            str(decision.get("recommended_process") or "unknown"),
            *[str(item) for item in _feature_tags(feature_map)],
            f"part_count={metrics.get('part_count')}",
            f"bbox={size}",
        ]
    ).strip()


def build_autonomous_engineering_bundle(
    *,
    file_id: str,
    geometry_metrics: dict[str, Any] | None,
    feature_map: dict[str, Any] | None,
    manufacturing_decision: dict[str, Any] | None,
    manufacturing_plan: dict[str, Any] | None,
    cost_estimate: dict[str, Any] | None,
    dfm_report: dict[str, Any] | None,
    assembly_structure: dict[str, Any] | None = None,
) -> dict[str, Any]:
    metrics = _as_dict(geometry_metrics)
    decision = _as_dict(manufacturing_decision)
    knowledge_base = load_default_knowledge_base()
    tags = [str(decision.get("recommended_process") or "").strip().lower(), *[item.lower() for item in _feature_tags(feature_map)]]
    knowledge_refs = knowledge_base.retrieve(
        _build_query(
            geometry_metrics=geometry_metrics,
            manufacturing_decision=manufacturing_decision,
            feature_map=feature_map,
        ),
        top_k=4,
        tags=[item for item in tags if item],
    )
    design_intent = build_design_intent(
        file_id=file_id,
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
        assembly_structure=assembly_structure,
        knowledge_refs=knowledge_refs,
    )
    autonomous_plan = build_autonomous_manufacturing_plan(
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
        manufacturing_decision=manufacturing_decision,
        base_plan=manufacturing_plan,
        knowledge_refs=knowledge_refs,
    )
    process_simulation = build_process_simulation(
        file_id=file_id,
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
        manufacturing_plan=autonomous_plan,
    )
    cost_optimization = build_cost_optimization(
        file_id=file_id,
        cost_estimate=cost_estimate,
        manufacturing_plan=autonomous_plan,
        process_simulation=process_simulation,
    )
    design_optimization = build_design_optimization(
        file_id=file_id,
        feature_map=feature_map,
        manufacturing_decision=manufacturing_decision,
        process_simulation=process_simulation,
    )
    engineering_decision = build_engineering_decision(
        file_id=file_id,
        manufacturing_decision=manufacturing_decision,
        manufacturing_plan=autonomous_plan,
        cost_estimate=cost_estimate,
        process_simulation=process_simulation,
        design_optimization=design_optimization,
        dfm_report=dfm_report,
        knowledge_refs=knowledge_refs,
    )
    engineering_master_report = build_engineering_master_report(
        file_id=file_id,
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
        manufacturing_decision=manufacturing_decision,
        manufacturing_plan=autonomous_plan,
        cost_estimate=cost_estimate,
        dfm_report=dfm_report,
        design_intent=design_intent,
        process_simulation=process_simulation,
        cost_optimization=cost_optimization,
        design_optimization=design_optimization,
        engineering_decision=engineering_decision,
        knowledge_refs=knowledge_refs,
    )
    return {
        "design_intent": design_intent,
        "manufacturing_plan": autonomous_plan,
        "process_simulation": process_simulation,
        "cost_optimization": cost_optimization,
        "design_optimization": design_optimization,
        "engineering_decision": engineering_decision,
        "engineering_master_report": engineering_master_report,
        "engineering_capabilities": {
            "design_interpreter": "enabled",
            "manufacturing_planner": "enabled",
            "process_simulation": "enabled",
            "cost_optimizer": "enabled",
            "design_optimizer": "enabled",
            "decision_synthesis": "enabled",
            "knowledge_base": knowledge_base.diagnostics(),
        },
        "engineering_pipeline": [
            {"stage": "geometry_analysis", "status": "completed"},
            {"stage": "feature_recognition", "status": "completed"},
            {"stage": "manufacturing_prediction", "status": "completed"},
            {"stage": "manufacturing_planning", "status": "completed"},
            {"stage": "process_simulation", "status": "completed"},
            {"stage": "cost_estimation", "status": "completed"},
            {"stage": "design_optimization", "status": "completed"},
            {"stage": "report_generation", "status": "completed"},
        ],
    }
