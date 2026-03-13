from __future__ import annotations

from app.core.autonomous_engineering.design_interpreter import build_design_intent


def test_design_interpreter_derives_design_intent_from_geometry_and_features() -> None:
    payload = build_design_intent(
        file_id="scx_test",
        geometry_metrics={
            "geometry_hash": "geom-1",
            "bbox": {"size": [120.0, 80.0, 20.0]},
            "part_count": 2,
            "volume": 1500.0,
        },
        feature_map={
            "features": {
                "holes": {"count": 4, "detection_mode": "proxy"},
                "threads": {"count": 2, "detection_mode": "proxy"},
                "thin_walls": {"count": 1, "detection_mode": "bounding_box_proxy"},
            }
        },
        assembly_structure={"mode": "mesh_approx", "occurrence_count": 2},
        knowledge_refs=[{"id": "kb1", "title": "CNC"}],
    )

    assert payload["file_id"] == "scx_test"
    assert payload["critical_dimensions"]["part_count"] == 2
    assert payload["functional_features"][0]["name"] == "holes"
    assert payload["manufacturing_sensitive_features"][0]["name"] in {"thin_walls", "threads"}
    assert payload["knowledge_refs"][0]["id"] == "kb1"
