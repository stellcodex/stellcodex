from __future__ import annotations

from types import SimpleNamespace
import unittest

from app.api.v1.routes.files import DecisionJsonOut, _build_scx_manifest
from app.workers.tasks import _assembly_meta, _is_ready_contract


class V7ContractTests(unittest.TestCase):
    def test_decision_output_model_contains_v7_keys(self) -> None:
        fields = set(DecisionJsonOut.model_fields.keys())
        required = {
            "rule_version",
            "mode",
            "confidence",
            "manufacturing_method",
            "rule_explanations",
            "conflict_flags",
            "state",
        }
        self.assertTrue(required.issubset(fields))

    def test_assembly_meta_contains_required_fields(self) -> None:
        payload = _assembly_meta("brep", 2, "demo.step")
        self.assertIn("occurrences", payload)
        self.assertIn("index", payload)
        self.assertIn("occurrence_id_to_gltf_nodes", payload["index"])

        first = payload["occurrences"][0]
        for key in ("occurrence_id", "part_id", "display_name", "selectable", "children"):
            self.assertIn(key, first)
        self.assertIsInstance(first["children"], list)
        self.assertIsInstance(first["selectable"], bool)

    def test_ready_contract_rejects_missing_assembly_meta(self) -> None:
        payload = {
            "assembly_meta_key": "metadata/file/assembly_meta.json",
            "preview_jpg_keys": ["p1.jpg", "p2.jpg", "p3.jpg"],
            "assembly_meta": {"occurrences": []},
        }
        self.assertFalse(_is_ready_contract("3d", payload, "converted/model.glb", "thumb.png"))

    def test_manifest_part_count_uses_occurrence_count(self) -> None:
        file_row = SimpleNamespace(
            file_id="scx_file_33333333-3333-3333-3333-333333333333",
            thumbnail_key=None,
            meta={
                "assembly_tree": [
                    {
                        "id": "occ_001",
                        "occurrence_id": "occ_001",
                        "part_id": "part_001",
                        "kind": "part",
                        "children": [],
                    },
                    {
                        "id": "occ_002",
                        "occurrence_id": "occ_002",
                        "part_id": "part_002",
                        "kind": "part",
                        "children": [],
                    },
                ],
                "geometry_meta_json": {"part_count": 999},
            },
        )
        manifest = _build_scx_manifest(file_row, lods={})
        self.assertEqual(manifest["part_count"], 2)


if __name__ == "__main__":
    unittest.main()
