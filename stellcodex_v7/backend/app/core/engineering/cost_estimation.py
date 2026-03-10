"""Deterministic engineering cost estimate helpers.

This baseline is intentionally simple and traceable. If pricing rules evolve,
update this file and the engineering reference docs together.
"""

from __future__ import annotations

import os
from typing import Any

from app.services.cost_estimator import CURRENCY, DEFAULT_MATERIAL, MATERIAL_DB


PROCESS_LABELS = {
    "cnc_machining": "CNC Machining",
    "injection_molding": "Injection Molding",
    "3d_printing": "3D Printing",
    "unknown": "Unknown",
}


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def build_cost_estimate(
    *,
    geometry_metrics: dict[str, Any] | None,
    feature_map: dict[str, Any] | None,
    manufacturing_decision: dict[str, Any] | None,
    manufacturing_plan: dict[str, Any] | None,
    quantity: int | None = None,
    material_id: str | None = None,
) -> dict[str, Any]:
    metrics = _as_dict(geometry_metrics)
    decision = _as_dict(manufacturing_decision)
    plan = _as_dict(manufacturing_plan)
    features = _as_dict(feature_map).get("features")
    features = features if isinstance(features, dict) else {}

    process = str(decision.get("recommended_process") or "unknown")
    qty = max(1, _as_int(quantity, 1))
    material_key = str(material_id or DEFAULT_MATERIAL)
    material = MATERIAL_DB.get(material_key) or MATERIAL_DB[DEFAULT_MATERIAL]
    if material_key not in MATERIAL_DB:
        material_key = DEFAULT_MATERIAL

    volume_mm3 = _as_float(metrics.get("volume"), 0.0)
    bbox = _as_dict(metrics.get("bbox"))
    if volume_mm3 <= 0.0 and isinstance(bbox.get("size"), list) and len(bbox.get("size")) >= 3:
        size = bbox["size"]
        volume_mm3 = _as_float(size[0]) * _as_float(size[1]) * _as_float(size[2])

    volume_cm3 = volume_mm3 / 1000.0
    density = _as_float(material.get("density"), 7.87)
    material_cost_per_kg = _as_float(material.get("eur_per_kg"), 2.5)
    raw_weight_kg = (volume_cm3 * density) / 1000.0
    material_cost = raw_weight_kg * material_cost_per_kg

    setup_count = max(1, _as_int(plan.get("setup_count"), 1))
    cycle_minutes = _as_float(plan.get("estimated_cycle_time_minutes"), 0.0)
    holes = _as_int(_as_dict(features.get("holes")).get("count"), 0)
    threads = _as_int(_as_dict(features.get("threads")).get("count"), 0)
    risk_score = _as_float(decision.get("dfm_risk_score"), 0.2)

    cnc_hourly = _as_float(os.getenv("ENGINEERING_RATE_CNC", "85.0"))
    molding_hourly = _as_float(os.getenv("ENGINEERING_RATE_MOLDING", "60.0"))
    printing_hourly = _as_float(os.getenv("ENGINEERING_RATE_PRINTING", "25.0"))
    injection_tooling_base = _as_float(os.getenv("ENGINEERING_INJECTION_TOOLING_BASE", "2500.0"))

    if process == "cnc_machining":
        setup_cost = setup_count * 120.0
        cycle_cost = (cycle_minutes / 60.0) * cnc_hourly
        tooling_cost = holes * 1.5 + threads * 4.0
    elif process == "injection_molding":
        setup_cost = setup_count * 180.0
        cycle_cost = (cycle_minutes / 60.0) * molding_hourly
        tooling_cost = injection_tooling_base
    elif process == "3d_printing":
        setup_cost = setup_count * 20.0
        cycle_cost = (cycle_minutes / 60.0) * printing_hourly
        tooling_cost = 0.0
    else:
        setup_cost = 0.0
        cycle_cost = 0.0
        tooling_cost = 0.0

    risk_multiplier = 1.0 + min(0.6, risk_score * 0.35)
    unit_direct = (material_cost + cycle_cost) * risk_multiplier
    amortized_setup = setup_cost / qty
    amortized_tooling = tooling_cost / qty if qty > 0 else tooling_cost
    estimated_unit_cost = round(unit_direct + amortized_setup + amortized_tooling, 2)
    estimated_batch_cost = round(estimated_unit_cost * qty, 2)

    if process == "unknown":
        confidence = 0.0
        capability_status = "degraded"
    elif process == "injection_molding" and qty < 50:
        confidence = 0.52
        capability_status = "degraded"
    else:
        confidence = min(0.94, round(_as_float(decision.get("confidence"), 0.0) * 0.9 + 0.08, 4))
        capability_status = str(decision.get("capability_status") or "supported")

    return {
        "currency": CURRENCY,
        "material_id": material_key,
        "material_label": str(material.get("label") or material_key),
        "recommended_process": process,
        "process_label": PROCESS_LABELS.get(process, process.title()),
        "quantity": qty,
        "estimated_unit_cost": estimated_unit_cost,
        "estimated_batch_cost": estimated_batch_cost,
        "cost_breakdown": {
            "raw_weight_kg": round(raw_weight_kg, 4),
            "material_cost": round(material_cost, 2),
            "setup_cost": round(setup_cost, 2),
            "tooling_cost": round(tooling_cost, 2),
            "cycle_cost_per_unit": round(cycle_cost, 2),
            "risk_multiplier": round(risk_multiplier, 4),
        },
        "cost_drivers": [
            f"process={process}",
            f"setup_count={setup_count}",
            f"holes={holes}",
            f"threads={threads}",
            f"risk_score={round(risk_score, 4)}",
        ],
        "confidence": confidence,
        "capability_status": capability_status,
    }
