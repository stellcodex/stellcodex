from __future__ import annotations

from app.core.autonomous_engineering.manufacturing_planner import build_autonomous_manufacturing_plan


def test_autonomous_manufacturing_planner_enriches_cnc_plan() -> None:
    payload = build_autonomous_manufacturing_plan(
        geometry_metrics={"part_count": 1},
        feature_map={"features": {"holes": {"count": 3}, "threads": {"count": 1}}},
        manufacturing_decision={"recommended_process": "cnc_machining"},
        base_plan={"recommended_process": "cnc_machining", "setup_count": 2, "quantity": 3},
        knowledge_refs=[{"id": "kb_cnc", "title": "CNC machining"}],
    )

    assert payload["recommended_process"] == "cnc_machining"
    assert payload["setup_count"] == 2
    assert "rough_machining" in payload["process_sequence"]
    assert payload["estimated_cycle_time_minutes"] > 0.0
    assert payload["knowledge_refs"][0]["id"] == "kb_cnc"
