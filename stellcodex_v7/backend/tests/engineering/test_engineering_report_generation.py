from __future__ import annotations

from app.core.engineering import (
    build_cost_estimate,
    build_engineering_dfm_report,
    build_engineering_report,
    build_feature_map,
    build_manufacturing_decision,
    build_manufacturing_plan,
    build_runtime_geometry_metrics,
)


def test_engineering_report_aggregates_pipeline_outputs() -> None:
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
    dfm_report = build_engineering_dfm_report(
        file_id="sample",
        mode="brep",
        confidence=0.92,
        rule_version="engineering_dfm.v1",
        rule_explanations=["deterministic engineering checks"],
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
        manufacturing_decision=decision,
        risk_analysis=[{"code": "thin_section_proxy", "severity": "medium"}],
        recommendations=["Review thin sections."],
        capability_status="supported",
        unavailable_reason=None,
    )

    report = build_engineering_report(
        file_id="sample",
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
        manufacturing_decision=decision,
        manufacturing_plan=plan,
        cost_estimate=estimate,
        dfm_report=dfm_report,
    )

    assert report["schema"] == "stellcodex.v1.engineering_report"
    assert report["manufacturing_recommendation"]["recommended_process"] == decision["recommended_process"]
    assert report["manufacturing_plan"]["recommended_process"] == decision["recommended_process"]
    assert report["cost_estimate"]["estimated_unit_cost"] == estimate["estimated_unit_cost"]
    assert report["dfm_report"]["risk_count"] == len(dfm_report["risks"])
    assert report["report_hash"]
