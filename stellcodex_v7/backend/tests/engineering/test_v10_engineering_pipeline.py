from __future__ import annotations

from app.core.autonomous_engineering.pipeline import build_autonomous_engineering_bundle


def test_v10_engineering_pipeline_produces_all_artifacts_and_report() -> None:
    bundle = build_autonomous_engineering_bundle(
        file_id="scx_test",
        geometry_metrics={
            "geometry_hash": "geom-1",
            "mode": "MESH_APPROX",
            "bbox": {"size": [120.0, 80.0, 30.0]},
            "part_count": 1,
            "volume": 9000.0,
        },
        feature_map={
            "features": {
                "holes": {"count": 3, "detection_mode": "proxy"},
                "threads": {"count": 1, "detection_mode": "proxy"},
                "thin_walls": {"count": 1, "detection_mode": "bounding_box_proxy"},
            }
        },
        manufacturing_decision={
            "recommended_process": "cnc_machining",
            "confidence": 0.83,
            "capability_status": "supported",
        },
        manufacturing_plan={"recommended_process": "cnc_machining", "setup_count": 2, "quantity": 4},
        cost_estimate={
            "currency": "EUR",
            "estimated_unit_cost": 24.5,
            "estimated_batch_cost": 98.0,
            "cost_drivers": ["setup_count=2"],
            "capability_status": "supported",
        },
        dfm_report={"risks": [{"code": "thin_wall_proxy", "severity": "medium"}], "recommended_changes": ["Review thin sections."]},
        assembly_structure={"mode": "mesh_approx", "occurrence_count": 1},
    )

    assert bundle["design_intent"]["functional_features"]
    assert bundle["manufacturing_plan"]["process_sequence"]
    assert bundle["process_simulation"]["machining_feasibility"] in {"feasible", "review_required"}
    assert bundle["cost_optimization"]["optimized_cost"] <= bundle["cost_optimization"]["baseline_cost"]
    assert bundle["design_optimization"]["status"] in {"actionable", "no_changes_required"}
    assert bundle["engineering_decision"]["recommended_process"] == "cnc_machining"
    assert bundle["engineering_master_report"]["manufacturing_recommendation"]["recommended_process"] == "cnc_machining"
    assert bundle["engineering_capabilities"]["knowledge_base"]["document_count"] >= 1
    assert bundle["engineering_pipeline"][-1]["stage"] == "report_generation"
