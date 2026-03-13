from __future__ import annotations

from app.core.autonomous_engineering.cost_optimizer import build_cost_optimization


def test_cost_optimization_reduces_baseline_when_setup_count_is_high() -> None:
    payload = build_cost_optimization(
        file_id="scx_test",
        cost_estimate={
            "currency": "EUR",
            "estimated_unit_cost": 22.5,
            "estimated_batch_cost": 225.0,
            "cost_drivers": ["setup_count=2"],
        },
        manufacturing_plan={"recommended_process": "cnc_machining", "setup_count": 2},
        process_simulation={"tool_accessibility": "limited", "setup_complexity": "medium"},
    )

    assert payload["baseline_cost"] == 225.0
    assert payload["optimized_cost"] < payload["baseline_cost"]
    assert payload["optimization_suggestions"]
