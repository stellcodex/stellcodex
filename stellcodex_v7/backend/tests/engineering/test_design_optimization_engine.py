from __future__ import annotations

from app.core.autonomous_engineering.design_optimizer import build_design_optimization


def test_design_optimization_emits_actionable_suggestions() -> None:
    payload = build_design_optimization(
        file_id="scx_test",
        feature_map={"features": {"thin_walls": {"count": 1}, "threads": {"count": 1}, "drafts": {"count": 0}}},
        manufacturing_decision={"recommended_process": "injection_molding"},
        process_simulation={"tool_accessibility": "poor"},
    )

    assert payload["status"] == "actionable"
    assert payload["suggestions"]
    assert any(item["id"] == "increase_draft_angle" for item in payload["suggestions"])
