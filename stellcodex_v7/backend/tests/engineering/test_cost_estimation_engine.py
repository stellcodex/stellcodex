from __future__ import annotations

from app.core.engineering import (
    build_cost_estimate,
    build_feature_map,
    build_manufacturing_decision,
    build_manufacturing_plan,
    build_runtime_geometry_metrics,
)


def test_cost_estimate_returns_positive_batch_cost_for_supported_process() -> None:
    geometry_metrics = build_runtime_geometry_metrics(
        file_id="sample",
        mode="brep",
        source_type="step_runtime",
        confidence=0.92,
        bbox={"size": [120.0, 80.0, 4.0]},
        volume=42000.0,
        surface_area=18000.0,
        part_count=1,
        triangle_count=None,
        metadata={"capability_status": "brep_ready"},
    )
    feature_map = build_feature_map(
        mode="brep",
        geometry_metrics=geometry_metrics,
        feature_flags={"hole_count": 2, "surface_breakdown": {"conical": 2}},
        source_signals={"thread_hints": []},
    )
    decision = build_manufacturing_decision(
        mode="brep",
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
        quantity=120,
    )
    plan = build_manufacturing_plan(
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
        manufacturing_decision=decision,
        quantity=120,
    )

    estimate = build_cost_estimate(
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
        manufacturing_decision=decision,
        manufacturing_plan=plan,
        quantity=120,
    )

    assert estimate["recommended_process"] == decision["recommended_process"]
    assert estimate["estimated_unit_cost"] > 0.0
    assert estimate["estimated_batch_cost"] >= estimate["estimated_unit_cost"]
    assert estimate["confidence"] > 0.0


def test_cost_estimate_fails_closed_for_unknown_process() -> None:
    geometry_metrics = build_runtime_geometry_metrics(
        file_id="sample",
        mode="visual_only",
        source_type="analysis_unavailable",
        confidence=0.1,
        bbox=None,
        volume=None,
        surface_area=None,
        part_count=None,
        triangle_count=None,
        metadata={"capability_status": "preview_only"},
    )
    feature_map = build_feature_map(
        mode="visual_only",
        geometry_metrics=geometry_metrics,
        feature_flags={},
        source_signals={},
    )
    decision = build_manufacturing_decision(
        mode="visual_only",
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
    )
    plan = build_manufacturing_plan(
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
        manufacturing_decision=decision,
    )

    estimate = build_cost_estimate(
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
        manufacturing_decision=decision,
        manufacturing_plan=plan,
    )

    assert estimate["recommended_process"] == "unknown"
    assert estimate["confidence"] == 0.0
    assert estimate["capability_status"] == "degraded"
