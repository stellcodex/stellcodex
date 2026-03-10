from __future__ import annotations

from app.core.engineering import (
    build_feature_map,
    build_manufacturing_decision,
    build_manufacturing_plan,
    build_runtime_geometry_metrics,
)


def test_manufacturing_plan_matches_deterministic_process_selection() -> None:
    geometry_metrics = build_runtime_geometry_metrics(
        file_id="sample",
        mode="brep",
        source_type="step_runtime",
        confidence=0.92,
        bbox={"size": [120.0, 80.0, 4.0]},
        volume=42000.0,
        surface_area=None,
        part_count=1,
        triangle_count=None,
        metadata={"capability_status": "brep_ready"},
    )
    feature_map = build_feature_map(
        mode="brep",
        geometry_metrics=geometry_metrics,
        feature_flags={"surface_breakdown": {"conical": 2}},
        source_signals={"thread_hints": []},
    )
    decision = build_manufacturing_decision(
        mode="brep",
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
        quantity=200,
    )

    plan = build_manufacturing_plan(
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
        manufacturing_decision=decision,
        quantity=200,
    )

    assert plan["recommended_process"] == "injection_molding"
    assert "mold_setup" in plan["process_sequence"]
    assert plan["estimated_cycle_time_minutes"] > 0.0
    assert plan["estimated_batch_time_minutes"] >= plan["estimated_cycle_time_minutes"]


def test_manufacturing_plan_falls_back_to_manual_review_for_unknown_process() -> None:
    plan = build_manufacturing_plan(
        geometry_metrics={},
        feature_map={},
        manufacturing_decision={"recommended_process": "unknown", "capability_status": "degraded"},
    )

    assert plan["recommended_process"] == "unknown"
    assert plan["process_sequence"][0] == "manual_review"
    assert plan["machine_requirements"] == ["manual engineering review"]
