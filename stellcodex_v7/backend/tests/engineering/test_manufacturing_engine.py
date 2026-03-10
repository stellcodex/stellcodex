from __future__ import annotations

from app.core.engineering import MODE_BREP, MODE_VISUAL_ONLY, build_feature_map, build_manufacturing_decision, build_runtime_geometry_metrics


def test_manufacturing_decision_prefers_injection_molding_for_high_volume_brep() -> None:
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
        feature_flags={"surface_breakdown": {"conical": 3}},
        source_signals={"thread_hints": []},
    )

    decision = build_manufacturing_decision(
        mode="brep",
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
        quantity=250,
    )

    assert feature_map["mode"] == MODE_BREP
    assert decision["recommended_process"] == "injection_molding"
    assert decision["capability_status"] == "supported"
    assert decision["confidence"] > 0.0


def test_manufacturing_decision_fails_closed_for_visual_only() -> None:
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
        quantity=10,
    )

    assert feature_map["mode"] == MODE_VISUAL_ONLY
    assert decision["recommended_process"] == "unknown"
    assert decision["capability_status"] == "degraded"
    assert "insufficient_geometry_fidelity" in decision["conflict_flags"]
