from __future__ import annotations

from app.core.autonomous_engineering.process_simulation import build_process_simulation


def test_process_simulation_flags_multi_setup_complexity() -> None:
    payload = build_process_simulation(
        file_id="scx_test",
        geometry_metrics={"geometry_hash": "geom-1", "part_count": 1},
        feature_map={"features": {"thin_walls": {"count": 1}, "threads": {"count": 2}}},
        manufacturing_plan={"recommended_process": "injection_molding", "setup_count": 2},
    )

    assert payload["machining_feasibility"] in {"feasible", "review_required"}
    assert payload["tool_accessibility"] in {"good", "limited", "poor"}
    assert payload["setup_complexity"] == "medium"
    assert payload["risk_flags"]
