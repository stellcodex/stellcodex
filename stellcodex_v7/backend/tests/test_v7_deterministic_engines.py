from __future__ import annotations

from types import SimpleNamespace
import unittest

from app.core.dfm_engine import build_dfm_pdf, build_dfm_report
from app.core.orchestrator import enforce_state_machine
from app.core.rule_engine import evaluate_deterministic_rules


class V7DeterministicEngineTests(unittest.TestCase):
    def test_rule_engine_returns_required_contract_fields(self) -> None:
        meta = {
            "quantity": 1200,
            "tolerance_mm": 0.02,
            "material_shrinkage_pct": 2.6,
            "geometry_meta_json": {
                "wall_min_mm": 0.6,
                "wall_max_mm": 4.2,
                "bbox": {"x": 180, "y": 140, "z": 90},
            },
            "geometry_report": {
                "draft_deg_min": 0.4,
                "undercut_count": 2,
            },
        }
        rules = {
            "quantity_threshold_high": 500,
            "tolerance_mm_tight": 0.05,
            "wall_mm_min": 1.0,
            "wall_mm_max": 3.0,
            "draft_min_deg": 1.0,
            "undercut_count_warn": 1,
            "shrinkage_warn_pct": 2.0,
            "shrinkage_block_pct": 4.0,
            "volume_mm3_high": 1000000,
            "volume_quantity_conflict_limit": 50000000,
        }
        results = evaluate_deterministic_rules(meta, rules)
        self.assertGreaterEqual(len(results), 7)
        for row in results:
            for key in (
                "rule_id",
                "triggered",
                "severity",
                "explanation",
                "reference",
                "deterministic_reasoning",
            ):
                self.assertIn(key, row)

    def test_dfm_engine_generates_json_and_pdf_with_required_metadata(self) -> None:
        file_row = SimpleNamespace(
            file_id="scx_file_44444444-4444-4444-4444-444444444444",
            meta={
                "material_shrinkage_pct": 2.5,
                "geometry_meta_json": {"wall_min_mm": 0.7, "wall_max_mm": 3.7},
                "geometry_report": {"draft_deg_min": 0.6, "undercut_count": 1},
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
        self.assertIn("wall_risks", report)
        self.assertIn("draft_risks", report)
        self.assertIn("undercut_risks", report)
        self.assertIn("shrinkage_warnings", report)
        self.assertIn("recommendations", report)
        self.assertEqual(report["mode"], "brep")
        self.assertEqual(report["rule_version"], "v7.0.0")
        self.assertIsInstance(report["rule_explanations"], list)
        pdf_bytes = build_dfm_pdf(report)
        self.assertTrue(pdf_bytes.startswith(b"%PDF-1.4"))

    def test_state_machine_blocks_skip_transitions(self) -> None:
        bounded_state, path, checkpoint = enforce_state_machine("S4", "S7")
        self.assertEqual(bounded_state, "S5")
        self.assertEqual(path, ["S4", "S5"])
        self.assertTrue(checkpoint)


if __name__ == "__main__":
    unittest.main()
