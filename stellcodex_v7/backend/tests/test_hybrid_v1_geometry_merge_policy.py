from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR_STR = str(BACKEND_DIR)
if BACKEND_DIR_STR not in sys.path:
    sys.path.insert(0, BACKEND_DIR_STR)

from app.core.hybrid_v1_geometry import (  # noqa: E402
    CRITICAL_GEOMETRY_FIELDS,
    _is_unknown,
    build_geometry_report_for_step,
)


class HybridV1GeometryMergePolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self._orig_override = os.environ.get("HYBRID_V1_OVERRIDE_PROVIDED")

    def tearDown(self) -> None:
        if self._orig_override is None:
            os.environ.pop("HYBRID_V1_OVERRIDE_PROVIDED", None)
        else:
            os.environ["HYBRID_V1_OVERRIDE_PROVIDED"] = self._orig_override

    def _make_step_file(self, tmp_dir: str) -> Path:
        path = Path(tmp_dir) / "sample.step"
        path.write_text(
            "ISO-10303-21;\n"
            "HEADER;\n"
            "ENDSEC;\n"
            "DATA;\n"
            "ADVANCED_FACE('id',(),$,.T.);\n"
            "ENDSEC;\n"
            "END-ISO-10303-21;\n",
            encoding="utf-8",
        )
        return path

    def test_prod_mode_only_fills_unknown_fields(self) -> None:
        os.environ.pop("HYBRID_V1_OVERRIDE_PROVIDED", None)
        with tempfile.TemporaryDirectory() as tmp_dir:
            step_path = self._make_step_file(tmp_dir)
            baseline = build_geometry_report_for_step(step_path)
            provided_inputs = {
                "wall_mm_min": 2.2,
                "complexity_risk": "DEMO_FORCE_HIGH",
            }
            result = build_geometry_report_for_step(step_path, provided_inputs=provided_inputs)

        geometry = result["geometry"]
        self.assertIn("wall_mm_min", CRITICAL_GEOMETRY_FIELDS)
        self.assertIn("complexity_risk", CRITICAL_GEOMETRY_FIELDS)
        self.assertTrue(_is_unknown("unknown"))
        self.assertFalse(_is_unknown(2.2))
        self.assertEqual(geometry["wall_mm_min"], 2.2)
        self.assertEqual(geometry["complexity_risk"], baseline["geometry"]["complexity_risk"])
        self.assertNotEqual(geometry["complexity_risk"], "DEMO_FORCE_HIGH")

    def test_demo_override_overwrites_non_unknown_fields(self) -> None:
        os.environ["HYBRID_V1_OVERRIDE_PROVIDED"] = "1"
        with tempfile.TemporaryDirectory() as tmp_dir:
            step_path = self._make_step_file(tmp_dir)
            baseline = build_geometry_report_for_step(step_path)
            provided_inputs = {
                "wall_mm_min": 1.4,
                "complexity_risk": "DEMO_FORCE_HIGH",
            }
            result = build_geometry_report_for_step(step_path, provided_inputs=provided_inputs)

        geometry = result["geometry"]
        self.assertEqual(geometry["wall_mm_min"], 1.4)
        self.assertEqual(geometry["complexity_risk"], "DEMO_FORCE_HIGH")
        self.assertNotEqual(geometry["complexity_risk"], baseline["geometry"]["complexity_risk"])


if __name__ == "__main__":
    unittest.main()
