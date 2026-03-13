from __future__ import annotations

from app.core.autonomous_engineering.decision_synthesis import build_engineering_decision


def test_decision_synthesis_combines_plan_cost_risks_and_recommendations() -> None:
    payload = build_engineering_decision(
        file_id="scx_test",
        manufacturing_decision={"recommended_process": "cnc_machining", "confidence": 0.82},
        manufacturing_plan={"recommended_process": "cnc_machining", "process_sequence": ["rough_machining"]},
        cost_estimate={"currency": "EUR", "estimated_unit_cost": 12.4, "estimated_batch_cost": 124.0},
        process_simulation={"risk_flags": [{"code": "multi_setup_flow", "severity": "medium"}]},
        design_optimization={
            "suggestions": [
                {"recommended_action": "Reduce setup count by consolidating orientations."},
            ]
        },
        dfm_report={"risks": [{"code": "thin_wall_proxy", "severity": "medium"}], "recommended_changes": ["Review thin sections."]},
        knowledge_refs=[{"id": "kb_cost", "title": "Cost"}],
    )

    assert payload["recommended_process"] == "cnc_machining"
    assert len(payload["design_risks"]) == 2
    assert "Review thin sections." in payload["design_recommendations"]
    assert payload["knowledge_refs"][0]["id"] == "kb_cost"
