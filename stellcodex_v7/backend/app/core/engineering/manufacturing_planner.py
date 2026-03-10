"""Deterministic manufacturing plan assembly helpers.

The plan here is a structured baseline for reports and persistence, not a CNC
toolpath generator. Keep process sequencing explicit and readable.
"""

from __future__ import annotations

from typing import Any


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def build_manufacturing_plan(
    *,
    geometry_metrics: dict[str, Any] | None,
    feature_map: dict[str, Any] | None,
    manufacturing_decision: dict[str, Any] | None,
    quantity: int | None = None,
) -> dict[str, Any]:
    metrics = _as_dict(geometry_metrics)
    features = _as_dict(feature_map).get("features")
    features = features if isinstance(features, dict) else {}
    decision = _as_dict(manufacturing_decision)
    process = str(decision.get("recommended_process") or "unknown")
    qty = max(1, _as_int(quantity, 1))
    part_count = _as_int(metrics.get("part_count"), 1) or 1
    holes = _as_int(_as_dict(features.get("holes")).get("count"), 0)
    threads = _as_int(_as_dict(features.get("threads")).get("count"), 0)
    thin_walls = _as_int(_as_dict(features.get("thin_walls")).get("count"), 0)

    steps: list[dict[str, Any]] = []
    machine_requirements: list[str] = []
    estimated_cycle_minutes = 0.0
    setup_count = 1

    if process == "cnc_machining":
        steps = [
            {"step": "raw_material_preparation", "type": "setup"},
            {"step": "rough_machining", "type": "machining"},
            {"step": "hole_and_thread_ops", "type": "machining"} if holes or threads else {"step": "finish_machining", "type": "machining"},
            {"step": "finish_machining", "type": "machining"},
            {"step": "inspection", "type": "quality"},
        ]
        machine_requirements = ["3-axis CNC mill"]
        if holes > 6 or threads > 0:
            machine_requirements.append("drilling/tapping station")
            setup_count = 2
        estimated_cycle_minutes = 18.0 + holes * 1.5 + threads * 2.0 + thin_walls * 2.0
    elif process == "injection_molding":
        steps = [
            {"step": "tooling_review", "type": "setup"},
            {"step": "mold_setup", "type": "setup"},
            {"step": "injection_cycle", "type": "production"},
            {"step": "cooling_and_ejection", "type": "production"},
            {"step": "trim_and_inspection", "type": "quality"},
        ]
        machine_requirements = ["injection molding press", "mold tooling"]
        setup_count = 2
        estimated_cycle_minutes = 2.5 + thin_walls * 0.3
    elif process == "3d_printing":
        steps = [
            {"step": "build_preparation", "type": "setup"},
            {"step": "print_job", "type": "production"},
            {"step": "support_removal", "type": "postprocess"},
            {"step": "surface_finish", "type": "postprocess"},
            {"step": "inspection", "type": "quality"},
        ]
        machine_requirements = ["industrial 3D printer"]
        setup_count = 1
        estimated_cycle_minutes = 45.0 + thin_walls * 3.0
    else:
        steps = [
            {"step": "manual_review", "type": "review"},
            {"step": "process_selection", "type": "review"},
            {"step": "inspection", "type": "quality"},
        ]
        machine_requirements = ["manual engineering review"]
        estimated_cycle_minutes = 0.0

    plan = {
        "recommended_process": process,
        "quantity": qty,
        "part_count": part_count,
        "process_sequence": [item["step"] for item in steps],
        "operation_steps": steps,
        "machine_requirements": machine_requirements,
        "setup_count": setup_count,
        "estimated_cycle_time_minutes": round(estimated_cycle_minutes, 3),
        "estimated_batch_time_minutes": round(estimated_cycle_minutes * qty * part_count, 3),
        "capability_status": str(decision.get("capability_status") or "degraded"),
    }
    return plan
