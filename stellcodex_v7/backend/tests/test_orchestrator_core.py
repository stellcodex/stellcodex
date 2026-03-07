from __future__ import annotations

from types import SimpleNamespace
import unittest

from app.services.orchestrator_engine import build_decision_json


def _file(status: str, kind: str = "3d", mode: str = "brep", extra_meta: dict | None = None):
    meta = {"kind": kind, "mode": mode}
    if extra_meta:
        meta.update(extra_meta)
    return SimpleNamespace(file_id="scx_file_12345678-1234-1234-1234-123456789abc", status=status, meta=meta)


def _rules() -> dict:
    return {
        "draft_min_deg": 1.0,
        "wall_mm_min": 1.0,
        "wall_mm_max": 3.0,
        "block_on_unknown_critical": True,
        "force_approval_on_visual_only": True,
        "allow_hot_runner": False,
    }


class OrchestratorCoreTests(unittest.TestCase):
    def test_ready_pass_becomes_s6(self) -> None:
        file_row = _file(
            "ready",
            extra_meta={
                "dfm_findings": {"status_gate": "PASS", "risk_flags": []},
                "geometry_report": {"critical_unknowns": []},
            },
        )
        decision = build_decision_json(file_row, _rules())
        self.assertEqual(decision["state_code"], "S6")
        self.assertEqual(decision["status_gate"], "PASS")
        self.assertFalse(decision["approval_required"])

    def test_unknown_critical_forces_manual_approval(self) -> None:
        file_row = _file(
            "ready",
            extra_meta={
                "dfm_findings": {"status_gate": "PASS", "risk_flags": []},
                "geometry_report": {"critical_unknowns": ["draft_deg_min"]},
            },
        )
        decision = build_decision_json(file_row, _rules())
        self.assertEqual(decision["state_code"], "S5")
        self.assertEqual(decision["status_gate"], "NEEDS_APPROVAL")
        self.assertIn("unknown_critical_geometry", decision["risk_flags"])

    def test_visual_only_requires_manual_approval(self) -> None:
        file_row = _file(
            "ready",
            mode="visual_only",
            extra_meta={"dfm_findings": {"status_gate": "PASS", "risk_flags": []}},
        )
        decision = build_decision_json(file_row, _rules())
        self.assertEqual(decision["state_code"], "S5")
        self.assertEqual(decision["status_gate"], "NEEDS_APPROVAL")
        self.assertIn("visual_only_mode", decision["risk_flags"])

    def test_failed_file_becomes_rejected_state(self) -> None:
        file_row = _file("failed")
        decision = build_decision_json(file_row, _rules())
        self.assertEqual(decision["state_code"], "S7")
        self.assertEqual(decision["status_gate"], "REJECTED")


if __name__ == "__main__":
    unittest.main()
