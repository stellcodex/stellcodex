from __future__ import annotations

from types import SimpleNamespace

from app.core.dfm_engine import build_dfm_report
from app.core.engineering import build_engineering_dfm_report, build_feature_map, build_manufacturing_decision, build_runtime_geometry_metrics


def test_engineering_dfm_report_contains_geometry_feature_and_manufacturing_sections() -> None:
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
        feature_flags={"hole_count": 2, "surface_breakdown": {"conical": 2}},
        source_signals={"thread_hints": []},
    )
    manufacturing = build_manufacturing_decision(
        mode="brep",
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
        quantity=120,
    )

    report = build_engineering_dfm_report(
        file_id="sample",
        mode="brep",
        confidence=0.92,
        rule_version="engineering_dfm.v1",
        rule_explanations=["deterministic engineering checks"],
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
        manufacturing_decision=manufacturing,
        risk_analysis=[{"code": "thin_section_proxy", "severity": "medium"}],
        recommendations=["Review thin sections."],
        capability_status="supported",
        unavailable_reason=None,
    )

    assert report["schema"] == "stellcodex.v7.dfm_report"
    assert report["geometry_summary"]["bbox"] == geometry_metrics["bbox"]
    assert report["feature_summary"]["features"]["holes"]["count"] == 2
    assert report["manufacturing_recommendation"]["recommended_process"]
    assert report["risks"]
    assert report["report_hash"]


def test_legacy_dfm_engine_merges_engineering_artifacts_when_present() -> None:
    geometry_metrics = build_runtime_geometry_metrics(
        file_id="sample",
        mode="brep",
        source_type="step_runtime",
        confidence=0.91,
        bbox={"size": [100.0, 60.0, 3.0]},
        volume=18000.0,
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
    manufacturing = build_manufacturing_decision(
        mode="brep",
        geometry_metrics=geometry_metrics,
        feature_map=feature_map,
        quantity=200,
    )
    file_row = SimpleNamespace(
        file_id="scx_file_66666666-6666-6666-6666-666666666666",
        meta={
            "material_shrinkage_pct": 2.5,
            "geometry_meta_json": {"wall_min_mm": 0.7, "wall_max_mm": 3.7},
            "geometry_report": {"draft_deg_min": 0.6, "undercut_count": 1},
            "engineering_geometry_metrics": geometry_metrics,
            "engineering_feature_map": feature_map,
            "engineering_analysis": {
                "mode": "brep",
                "confidence": 0.91,
                "capability_status": "supported",
                "manufacturing_decision": manufacturing,
                "dfm_risk": [{"code": "thin_section_proxy", "severity": "medium"}],
                "recommendations": ["Review thin sections."],
            },
        },
    )
    rules = {
        "rule_version": "v7.0.0",
        "draft_min_deg": 1.0,
        "wall_mm_min": 1.0,
        "wall_mm_max": 3.0,
        "shrinkage_warn_pct": 2.0,
    }
    decision_json = {
        "mode": "brep",
        "confidence": 0.91,
        "rule_version": "v7.0.0",
        "rule_explanations": ["deterministic checks"],
    }

    report = build_dfm_report(file_row, rules, decision_json, deterministic_rules=[])

    assert report["manufacturing_recommendation"]["recommended_process"]
    assert report["feature_summary"]["features"]["drafts"]["count"] == 2
    assert report["wall_risks"]
    assert report["decision_json"]["mode"] == "brep"
