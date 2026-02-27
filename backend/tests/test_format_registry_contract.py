from __future__ import annotations

import unittest

from app.core.format_registry import (
    as_public_rows,
    get_rule_by_ext,
    grouped_payload,
    infer_mime_from_bytes,
    match_content_type,
)


class FormatRegistryContractTests(unittest.TestCase):
    def test_required_modes_present(self) -> None:
        self.assertEqual(get_rule_by_ext("step").mode, "brep")
        self.assertEqual(get_rule_by_ext("stl").mode, "mesh_approx")
        self.assertEqual(get_rule_by_ext("glb").mode, "visual_only")
        self.assertEqual(get_rule_by_ext("dxf").mode, "2d_only")
        self.assertEqual(get_rule_by_ext("docx").kind, "doc")

    def test_rejected_formats_include_reason(self) -> None:
        groups = grouped_payload()
        rejected = groups.get("rejected") or []
        self.assertTrue(any(item.get("ext") == "dwg" and item.get("reason") for item in rejected))

    def test_public_rows_have_no_missing_contract_fields(self) -> None:
        rows = as_public_rows()
        self.assertTrue(rows)
        required = {"ext", "kind", "mode", "pipeline", "accept", "display_label"}
        for row in rows:
            self.assertTrue(required.issubset(row.keys()))

    def test_mime_sniff_guards(self) -> None:
        sniffed = infer_mime_from_bytes(b"%PDF-1.4\n", "sample.pdf")
        self.assertEqual(sniffed, "application/pdf")
        self.assertTrue(match_content_type("application/pdf", "pdf"))
        self.assertFalse(match_content_type("image/png", "step"))


if __name__ == "__main__":
    unittest.main()
