"""Autonomous manufacturing plan enrichment."""

from __future__ import annotations

from typing import Any


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


def _build_operation_steps(process: str, *, holes: int, threads: int) -> list[dict[str, Any]]:
    if process == "cnc_machining":
        middle_step = "hole_and_thread_ops" if holes or threads else "feature_finishing"
        return [
            {"step": "material_preparation", "type": "setup", "duration_minutes": 6.0},
            {"step": "rough_machining", "type": "machining", "duration_minutes": 10.0},
            {"step": middle_step, "type": "machining", "duration_minutes": 4.0 + holes * 1.2 + threads * 1.6},
            {"step": "finishing_operations", "type": "machining", "duration_minutes": 5.5},
            {"step": "inspection", "type": "quality", "duration_minutes": 3.0},
        ]
    if process == "injection_molding":
        return [
            {"step": "material_preparation", "type": "setup", "duration_minutes": 3.0},
            {"step": "tooling_setup", "type": "setup", "duration_minutes": 12.0},
            {"step": "injection_cycle", "type": "production", "duration_minutes": 1.8},
            {"step": "cooling_and_ejection", "type": "production", "duration_minutes": 0.9},
            {"step": "inspection", "type": "quality", "duration_minutes": 1.2},
        ]
    if process == "3d_printing":
        return [
            {"step": "material_preparation", "type": "setup", "duration_minutes": 2.5},
            {"step": "build_setup", "type": "setup", "duration_minutes": 5.0},
            {"step": "print_run", "type": "production", "duration_minutes": 45.0},
            {"step": "post_processing", "type": "postprocess", "duration_minutes": 12.0},
            {"step": "inspection", "type": "quality", "duration_minutes": 2.5},
        ]
    return [
        {"step": "engineering_review", "type": "review", "duration_minutes": 10.0},
        {"step": "process_selection", "type": "review", "duration_minutes": 8.0},
        {"step": "inspection", "type": "quality", "duration_minutes": 2.0},
    ]


def build_autonomous_manufacturing_plan(
    *,
    geometry_metrics: dict[str, Any] | None,
    feature_map: dict[str, Any] | None,
    manufacturing_decision: dict[str, Any] | None,
    base_plan: dict[str, Any] | None,
    knowledge_refs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    metrics = _as_dict(geometry_metrics)
    features = _as_dict(_as_dict(feature_map).get("features"))
    decision = _as_dict(manufacturing_decision)
    plan = dict(_as_dict(base_plan))
    process = str(decision.get("recommended_process") or plan.get("recommended_process") or "unknown")
    holes = _as_int(_as_dict(features.get("holes")).get("count"))
    threads = _as_int(_as_dict(features.get("threads")).get("count"))
    setup_count = max(1, _as_int(plan.get("setup_count"), 1))
    operation_steps = _build_operation_steps(process, holes=holes, threads=threads)
    estimated_cycle_time_minutes = _as_float(plan.get("estimated_cycle_time_minutes"), 0.0)
    if estimated_cycle_time_minutes <= 0.0:
        estimated_cycle_time_minutes = round(sum(_as_float(step.get("duration_minutes")) for step in operation_steps), 3)
    machine_requirements = plan.get("machine_requirements")
    if not isinstance(machine_requirements, list) or not machine_requirements:
        if process == "cnc_machining":
            machine_requirements = ["3-axis CNC mill"]
        elif process == "injection_molding":
            machine_requirements = ["injection molding press", "mold tooling"]
        elif process == "3d_printing":
            machine_requirements = ["industrial 3D printer"]
        else:
            machine_requirements = ["manual engineering review"]
    plan.update(
        {
            "recommended_process": process,
            "process_sequence": [str(step["step"]) for step in operation_steps],
            "machine_requirements": machine_requirements,
            "operation_steps": operation_steps,
            "estimated_cycle_time_minutes": round(estimated_cycle_time_minutes, 3),
            "estimated_cycle_time": round(estimated_cycle_time_minutes, 3),
            "estimated_batch_time_minutes": round(
                max(1, _as_int(plan.get("quantity"), 1)) * max(1, _as_int(metrics.get("part_count"), 1)) * estimated_cycle_time_minutes,
                3,
            ),
            "setup_count": setup_count,
            "workflow_version": "stellcodex.v10.manufacturing_plan",
            "knowledge_refs": list(knowledge_refs or []),
        }
    )
    return plan
