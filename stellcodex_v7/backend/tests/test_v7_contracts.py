from __future__ import annotations

from types import SimpleNamespace
import unittest

from app.api.v1.routes.files import DecisionJsonOut, _build_scx_manifest, _is_valid_assembly_meta
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

    def test_ready_contract_rejects_duplicate_occurrence_ids(self) -> None:
        assembly_meta = {
            "occurrences": [
                {
                    "occurrence_id": "occ_001",
                    "part_id": "part_a",
                    "display_name": "A",
                    "selectable": True,
                    "children": [],
                },
                {
                    "occurrence_id": "occ_001",
                    "part_id": "part_b",
                    "display_name": "B",
                    "selectable": True,
                    "children": [],
                },
            ],
            "index": {
                "occurrence_id_to_gltf_nodes": {
                    "occ_001": ["node_1"],
                }
            },
        }
        payload = {
            "assembly_meta_key": "metadata/file/assembly_meta.json",
            "preview_jpg_keys": ["p1.jpg", "p2.jpg", "p3.jpg"],
            "assembly_meta": assembly_meta,
        }
        self.assertFalse(_is_ready_contract("3d", payload, "converted/model.glb", "thumb.png"))
        self.assertFalse(_is_valid_assembly_meta(assembly_meta))

    def test_ready_contract_rejects_unknown_child_reference(self) -> None:
        assembly_meta = {
            "occurrences": [
                {
                    "occurrence_id": "occ_001",
                    "part_id": "part_a",
                    "display_name": "A",
                    "selectable": True,
                    "children": ["occ_missing"],
                }
            ],
            "index": {"occurrence_id_to_gltf_nodes": {"occ_001": ["node_1"]}},
        }
        payload = {
            "assembly_meta_key": "metadata/file/assembly_meta.json",
            "preview_jpg_keys": ["p1.jpg", "p2.jpg", "p3.jpg"],
            "assembly_meta": assembly_meta,
        }
        self.assertFalse(_is_ready_contract("3d", payload, "converted/model.glb", "thumb.png"))
        self.assertFalse(_is_valid_assembly_meta(assembly_meta))

    def test_ready_contract_rejects_cyclic_parent_child_graph(self) -> None:
        assembly_meta = {
            "occurrences": [
                {
                    "occurrence_id": "occ_001",
                    "part_id": "part_a",
                    "display_name": "A",
                    "selectable": True,
                    "children": ["occ_002"],
                },
                {
                    "occurrence_id": "occ_002",
                    "part_id": "part_b",
                    "display_name": "B",
                    "selectable": True,
                    "children": ["occ_001"],
                },
            ],
            "index": {
                "occurrence_id_to_gltf_nodes": {
                    "occ_001": ["node_1"],
                    "occ_002": ["node_2"],
                }
            },
        }
        payload = {
            "assembly_meta_key": "metadata/file/assembly_meta.json",
            "preview_jpg_keys": ["p1.jpg", "p2.jpg", "p3.jpg"],
            "assembly_meta": assembly_meta,
        }
        self.assertFalse(_is_ready_contract("3d", payload, "converted/model.glb", "thumb.png"))
        self.assertFalse(_is_valid_assembly_meta(assembly_meta))

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

    def test_manifest_part_count_ignores_nonselectable_nodes_and_mesh_counts(self) -> None:
        file_row = SimpleNamespace(
            file_id="scx_file_44444444-4444-4444-4444-444444444444",
            thumbnail_key=None,
            meta={
                "assembly_tree": [
                    {
                        "id": "occ_001",
                        "occurrence_id": "occ_001",
                        "part_id": "part_001",
                        "kind": "part",
                        "selectable": True,
                        "children": [],
                    },
                    {
                        "id": "occ_002",
                        "occurrence_id": "occ_002",
                        "part_id": "part_002",
                        "kind": "part",
                        "selectable": False,
                        "children": [],
                    },
                ],
                "geometry_meta_json": {"part_count": 999},
                "lod_stats": {"lod0": {"mesh_count_assimp": 1234, "triangle_count": 9000}},
            },
        )
        manifest = _build_scx_manifest(file_row, lods={})
        self.assertEqual(manifest["part_count"], 1)
        self.assertEqual(manifest["stats"]["lod0"]["part_count"], 1)


if __name__ == "__main__":
    unittest.main()
