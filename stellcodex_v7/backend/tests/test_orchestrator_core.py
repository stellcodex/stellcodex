from __future__ import annotations

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from app.core.orchestrator import ensure_session_decision
from app.services.orchestrator_engine import build_decision_json


def _file(status: str, kind: str = "3d", mode: str = "brep", extra_meta: dict | None = None):
    meta = {"kind": kind, "mode": mode}
    if extra_meta:
        meta.update(extra_meta)
    return SimpleNamespace(file_id="scx_file_12345678-1234-1234-1234-123456789abc", status=status, meta=meta)


def _rules() -> dict:
    return {
        "rule_version": "v7.0.0",
        "draft_min_deg": 1.0,
        "wall_mm_min": 1.0,
        "wall_mm_max": 3.0,
        "block_on_unknown_critical": True,
        "force_approval_on_visual_only": True,
        "allow_hot_runner": False,
        "legacy_backfill_confidence": 0.05,
        "manufacturing_unknown_confidence_floor": 0.1,
        "manufacturing_fallback_method": "manual_review",
        "quantity_threshold_high": 500,
        "tolerance_mm_tight": 0.05,
        "undercut_count_warn": 1,
        "shrinkage_warn_pct": 2.0,
        "shrinkage_block_pct": 4.0,
        "volume_mm3_high": 1000000,
        "volume_quantity_conflict_limit": 50000000,
    }


class OrchestratorCoreTests(unittest.TestCase):
    def test_decision_contract_fields_are_present(self) -> None:
        file_row = _file("ready")
        decision = build_decision_json(file_row, _rules())
        for key in (
            "rule_version",
            "mode",
            "confidence",
            "manufacturing_method",
            "rule_explanations",
            "conflict_flags",
            "state",
        ):
            self.assertIn(key, decision)
        self.assertIsInstance(decision["rule_explanations"], list)
        self.assertIsInstance(decision["conflict_flags"], list)
        self.assertGreaterEqual(decision["confidence"], 0.0)
        self.assertLessEqual(decision["confidence"], 1.0)

    def test_ready_pass_becomes_s6(self) -> None:
        file_row = _file(
            "ready",
            extra_meta={
                "dfm_findings": {"status_gate": "PASS", "risk_flags": []},
                "geometry_report": {"critical_unknowns": []},
            },
        )
        decision = build_decision_json(file_row, _rules())
        self.assertEqual(decision["state"], "S6")
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
        self.assertEqual(decision["state"], "S5")
        self.assertEqual(decision["status_gate"], "NEEDS_APPROVAL")
        self.assertIn("unknown_critical_geometry", decision["risk_flags"])

    def test_visual_only_requires_manual_approval(self) -> None:
        file_row = _file(
            "ready",
            mode="visual_only",
            extra_meta={"dfm_findings": {"status_gate": "PASS", "risk_flags": []}},
        )
        decision = build_decision_json(file_row, _rules())
        self.assertEqual(decision["state"], "S5")
        self.assertEqual(decision["status_gate"], "NEEDS_APPROVAL")
        self.assertIn("visual_only_mode", decision["risk_flags"])

    def test_failed_file_stays_dfm_ready_rejected(self) -> None:
        file_row = _file("failed")
        decision = build_decision_json(file_row, _rules())
        self.assertEqual(decision["state"], "S4")
        self.assertEqual(decision["status_gate"], "REJECTED")

    def test_manual_approval_keeps_s7_when_required_inputs_pending(self) -> None:
        file_row = SimpleNamespace(
            file_id="scx_file_99999999-9999-9999-9999-999999999999",
            meta={"kind": "3d", "mode": "visual_only", "approval_override": "approved"},
            decision_json={},
        )
        existing = SimpleNamespace(
            state="S7",
            decision_json={
                "state": "S7",
                "state_code": "S7",
                "state_label": "share_ready",
                "status_gate": "PASS",
                "approval_required": False,
                "decision": "approve_manual",
                "rule_version": "v7.0.0",
                "mode": "visual_only",
                "confidence": 0.4,
                "manufacturing_method": "cnc_milling",
                "risk_flags": [],
                "conflict_flags": [],
                "rule_explanations": [],
            },
        )
        persisted = SimpleNamespace(id="session-1", state="S7")

        class _Query:
            def filter(self, *_args, **_kwargs):
                return self

            def first(self):
                return existing

        class _DB:
            def query(self, *_args, **_kwargs):
                return _Query()

            def add(self, *_args, **_kwargs):
                return None

            def flush(self):
                return None

            def commit(self):
                return None

            def refresh(self, _row):
                return None

        db = _DB()
        with patch("app.core.orchestrator.load_rule_config_map", return_value=_rules()), \
             patch("app.core.orchestrator.normalize_decision_json", return_value=existing.decision_json), \
             patch("app.core.orchestrator.evaluate_deterministic_rules", return_value=[]), \
             patch("app.core.orchestrator.build_dfm_report", return_value={"report_hash": "h", "schema": "s"}), \
             patch("app.core.orchestrator.build_dfm_pdf", return_value=b"%PDF"), \
             patch("app.core.orchestrator.upsert_orchestrator_session", return_value=persisted), \
             patch("app.core.orchestrator.log_event", return_value=None):
            _row, decision = ensure_session_decision(db, file_row)

        self.assertEqual(decision["state"], "S7")
        self.assertEqual(decision["status_gate"], "PASS")
        self.assertFalse(decision["approval_required"])
        self.assertIn("required_inputs_acknowledged_by_manual_approval", " ".join(decision["rule_explanations"]))


if __name__ == "__main__":
    unittest.main()
