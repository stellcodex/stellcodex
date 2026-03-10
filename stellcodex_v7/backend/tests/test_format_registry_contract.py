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
        self.assertEqual(get_rule_by_ext("html").kind, "doc")

    def test_rejected_formats_include_reason(self) -> None:
        groups = grouped_payload()
        rejected = groups.get("rejected") or []
        self.assertTrue(any(item.get("ext") == "dwg" and item.get("reason") for item in rejected))

    def test_public_rows_have_no_missing_contract_fields(self) -> None:
        rows = as_public_rows()
        self.assertTrue(rows)
        required = {
            "ext",
            "kind",
            "mode",
            "pipeline",
            "accept",
            "display_label",
            "support_tier",
            "preview_supported",
            "metadata_extracted",
            "geometry_extracted",
            "dfm_supported",
        }
        for row in rows:
            self.assertTrue(required.issubset(row.keys()))

    def test_capability_tiers_are_honest_for_real_supported_formats(self) -> None:
        rows = {row["ext"]: row for row in as_public_rows()}
        self.assertEqual(rows["step"]["support_tier"], "dfm_supported")
        self.assertTrue(rows["step"]["geometry_extracted"])
        self.assertEqual(rows["stl"]["support_tier"], "dfm_supported")
        self.assertEqual(rows["obj"]["support_tier"], "dfm_supported")
        self.assertEqual(rows["dxf"]["support_tier"], "dfm_supported")
        self.assertEqual(rows["pdf"]["support_tier"], "dfm_supported")
        self.assertEqual(rows["docx"]["support_tier"], "dfm_supported")
        self.assertEqual(rows["glb"]["support_tier"], "preview_supported")
        self.assertEqual(rows["iges"]["support_tier"], "accepted_only")

    def test_mime_sniff_guards(self) -> None:
        sniffed = infer_mime_from_bytes(b"%PDF-1.4\n", "sample.pdf")
        self.assertEqual(sniffed, "application/pdf")
        self.assertTrue(match_content_type("application/pdf", "pdf"))
        self.assertTrue(match_content_type("text/html", "html"))
        self.assertFalse(match_content_type("image/png", "step"))


if __name__ == "__main__":
    unittest.main()
