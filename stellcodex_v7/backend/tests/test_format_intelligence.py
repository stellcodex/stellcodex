from __future__ import annotations

import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from zipfile import ZIP_DEFLATED, ZipFile

import ezdxf

from app.core.events import EventEnvelope
from app.core.format_intelligence import extract_format_intelligence
from app.workers import tasks


def _cube_ascii_stl() -> bytes:
    return b"""solid cube
facet normal 0 0 1
 outer loop
  vertex 0 0 0
  vertex 1 0 0
  vertex 0 1 0
 endloop
endfacet
facet normal 0 0 1
 outer loop
  vertex 1 0 0
  vertex 1 1 0
  vertex 0 1 0
 endloop
endfacet
facet normal 0 0 -1
 outer loop
  vertex 0 0 1
  vertex 0 1 1
  vertex 1 0 1
 endloop
endfacet
facet normal 0 0 -1
 outer loop
  vertex 1 0 1
  vertex 0 1 1
  vertex 1 1 1
 endloop
endfacet
facet normal 0 1 0
 outer loop
  vertex 0 1 0
  vertex 1 1 0
  vertex 0 1 1
 endloop
endfacet
facet normal 0 1 0
 outer loop
  vertex 1 1 0
  vertex 1 1 1
  vertex 0 1 1
 endloop
endfacet
facet normal 0 -1 0
 outer loop
  vertex 0 0 0
  vertex 0 0 1
  vertex 1 0 0
 endloop
endfacet
facet normal 0 -1 0
 outer loop
  vertex 1 0 0
  vertex 0 0 1
  vertex 1 0 1
 endloop
endfacet
facet normal 1 0 0
 outer loop
  vertex 1 0 0
  vertex 1 0 1
  vertex 1 1 0
 endloop
endfacet
facet normal 1 0 0
 outer loop
  vertex 1 1 0
  vertex 1 0 1
  vertex 1 1 1
 endloop
endfacet
facet normal -1 0 0
 outer loop
  vertex 0 0 0
  vertex 0 1 0
  vertex 0 0 1
 endloop
endfacet
facet normal -1 0 0
 outer loop
  vertex 0 1 0
  vertex 0 1 1
  vertex 0 0 1
 endloop
endfacet
endsolid cube
"""


def _cube_obj() -> bytes:
    return b"""o cube
v 0 0 0
v 1 0 0
v 1 1 0
v 0 1 0
v 0 0 1
v 1 0 1
v 1 1 1
v 0 1 1
f 1 2 3
f 1 3 4
f 5 7 6
f 5 8 7
f 1 5 6
f 1 6 2
f 2 6 7
f 2 7 3
f 3 7 8
f 3 8 4
f 4 8 5
f 4 5 1
"""


def _minimal_step() -> bytes:
    return (
        "ISO-10303-21;\n"
        "HEADER;\n"
        "FILE_DESCRIPTION(('sample'),'2;1');\n"
        "FILE_NAME('sample.step','2026-03-10T00:00:00',('SCX'),('SCX'),'','','');\n"
        "FILE_SCHEMA(('CONFIG_CONTROL_DESIGN'));\n"
        "ENDSEC;\n"
        "DATA;\n"
        "#1=CARTESIAN_POINT('',(0.,0.,0.));\n"
        "#2=CARTESIAN_POINT('',(10.,0.,0.));\n"
        "#3=CARTESIAN_POINT('',(10.,5.,0.));\n"
        "#4=CARTESIAN_POINT('',(0.,5.,2.));\n"
        "#5=MANIFOLD_SOLID_BREP('',#10);\n"
        "#6=PRODUCT('ID','Bracket','',());\n"
        "#7=ADVANCED_FACE('',(),$,.T.);\n"
        "ENDSEC;\n"
        "END-ISO-10303-21;\n"
    ).encode("utf-8")


def _simple_docx_bytes(text: str) -> bytes:
    from io import BytesIO

    payload = BytesIO()
    with ZipFile(payload, mode="w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(
            "[Content_Types].xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>""",
        )
        archive.writestr(
            "_rels/.rels",
            """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>""",
        )
        archive.writestr(
            "word/document.xml",
            f"""<?xml version="1.0" encoding="UTF-8"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>{text}</w:t></w:r></w:p>
  </w:body>
</w:document>""",
        )
    return payload.getvalue()


def _make_dxf(path: Path) -> None:
    doc = ezdxf.new("R2010")
    doc.header["$INSUNITS"] = 4
    msp = doc.modelspace()
    msp.add_line((0, 0), (100, 0), dxfattribs={"layer": "OUTLINE"})
    msp.add_line((100, 0), (100, 60), dxfattribs={"layer": "OUTLINE"})
    msp.add_text("REV: A", dxfattribs={"height": 2.5, "layer": "NOTES"}).set_placement((0, 70))
    msp.add_text("MATERIAL: AL6061", dxfattribs={"height": 2.5, "layer": "NOTES"}).set_placement((0, 75))
    msp.add_text("TOL +/-0.1", dxfattribs={"height": 2.5, "layer": "NOTES"}).set_placement((0, 80))
    msp.add_text("100 mm", dxfattribs={"height": 2.5, "layer": "DIM"}).set_placement((0, 85))
    doc.blocks.new("TITLEBLOCK")
    doc.saveas(path)


def _write(path: Path, payload: bytes) -> Path:
    path.write_bytes(payload)
    return path


class _FakeQuery:
    def __init__(self, row) -> None:
        self.row = row

    def filter(self, *_args, **_kwargs):
        return self

    def first(self):
        return self.row


class _FakeDb:
    def __init__(self, row) -> None:
        self.row = row
        self.commits = 0

    def query(self, *_args, **_kwargs):
        return _FakeQuery(self.row)

    def add(self, *_args, **_kwargs):
        return None

    def commit(self) -> None:
        self.commits += 1

    def refresh(self, _row) -> None:
        return None


class _FakeS3:
    def __init__(self, payload: bytes) -> None:
        self.payload = payload
        self.puts: list[tuple[str, str, bytes, str]] = []

    def download_file(self, _bucket: str, _key: str, target: str) -> None:
        Path(target).write_bytes(self.payload)

    def put_object(self, *, Bucket: str, Key: str, Body: bytes, ContentType: str) -> None:
        self.puts.append((Bucket, Key, bytes(Body), ContentType))

    def upload_file(self, *_args, **_kwargs) -> None:
        return None


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


class FormatIntelligenceTests(unittest.TestCase):
    def test_classification_matrix_matches_real_support_tiers(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            cases = [
                ("part.stl", _cube_ascii_stl(), "model/stl", "dfm_supported", "cad_3d_ingest"),
                ("part.obj", _cube_obj(), "model/obj", "dfm_supported", "cad_3d_ingest"),
                ("part.step", _minimal_step(), "application/step", "dfm_supported", "cad_3d_ingest"),
                ("drawing.dxf", None, "application/dxf", "dfm_supported", "cad_2d_ingest"),
                ("drawing.pdf", tasks._simple_pdf_bytes("DWG", ["REV A", "MATERIAL: STEEL"]), "application/pdf", "dfm_supported", "document_ingest"),
                ("notes.docx", _simple_docx_bytes("REV B MATERIAL ABS CNC"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "dfm_supported", "document_ingest"),
                ("scene.glb", b"glTF", "model/gltf-binary", "preview_supported", "cad_3d_ingest"),
                ("legacy.iges", b"IGES", "application/octet-stream", "accepted_only", "cad_3d_ingest"),
            ]
            for name, payload, mime_type, tier, pipeline in cases:
                with self.subTest(name=name):
                    path = root / name
                    if name.endswith(".dxf"):
                        _make_dxf(path)
                    else:
                        _write(path, payload or b"")
                    result = extract_format_intelligence(
                        path,
                        file_id="scx_file_aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                        tenant_id=7,
                        original_filename=name,
                        mime_type=mime_type,
                        size_bytes=path.stat().st_size,
                    )
                    self.assertEqual(result["support_tier"], tier)
                    self.assertEqual(result["chosen_pipeline"], pipeline)

    def test_mesh_extraction_for_stl_and_obj_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            cases = [
                ("part.stl", _cube_ascii_stl(), "model/stl"),
                ("part.obj", _cube_obj(), "model/obj"),
            ]
            for name, payload, mime_type in cases:
                with self.subTest(name=name):
                    path = _write(root / name, payload)
                    left = extract_format_intelligence(
                        path,
                        file_id="scx_file_bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                        tenant_id=7,
                        original_filename=name,
                        mime_type=mime_type,
                        size_bytes=path.stat().st_size,
                    )
                    right = extract_format_intelligence(
                        path,
                        file_id="scx_file_bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                        tenant_id=7,
                        original_filename=name,
                        mime_type=mime_type,
                        size_bytes=path.stat().st_size,
                    )
                    self.assertEqual(left, right)
                    self.assertEqual(left["extraction_status"], "completed")
                    self.assertTrue(left["geometry_extracted"])
                    self.assertEqual(left["triangle_count"], 12)
                    self.assertEqual(left["face_count"], 12)
                    self.assertEqual(left["vertex_count"], 8)
                    self.assertTrue(any(rule["rule_id"] == "units_missing" for rule in left["engineering_rules"]))

    def test_step_extraction_reports_geometry_and_safe_rules(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = _write(Path(tmp_dir) / "part.step", _minimal_step())
            result = extract_format_intelligence(
                path,
                file_id="scx_file_cccccccc-cccc-cccc-cccc-cccccccccccc",
                tenant_id=7,
                original_filename="part.step",
                mime_type="application/step",
                size_bytes=path.stat().st_size,
            )

        self.assertEqual(result["extraction_status"], "completed")
        self.assertEqual(result["support_tier"], "dfm_supported")
        self.assertTrue(result["geometry_extracted"])
        self.assertEqual(result["detected_units"], "mm")
        self.assertEqual(result["part_count"], 1)
        self.assertEqual(result["body_count"], 1)
        self.assertEqual(result["face_count"], 1)
        self.assertIn("bbox", result)

    def test_dxf_extraction_collects_counts_text_and_units(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "drawing.dxf"
            _make_dxf(path)
            result = extract_format_intelligence(
                path,
                file_id="scx_file_dddddddd-dddd-dddd-dddd-dddddddddddd",
                tenant_id=7,
                original_filename="drawing.dxf",
                mime_type="application/dxf",
                size_bytes=path.stat().st_size,
            )

        self.assertEqual(result["extraction_status"], "completed")
        self.assertTrue(result["metadata_extracted"])
        self.assertEqual(result["units"], "millimeters")
        self.assertGreaterEqual(result["entity_count"], 4)
        self.assertGreaterEqual(result["layer_count"], 1)
        self.assertGreaterEqual(result["block_count"], 1)
        self.assertIn("AL6061", " ".join(result["material_mentions"]))
        self.assertTrue(any("REV" in item.upper() for item in result["revision_mentions"]))
        self.assertTrue(result["dimension_text"])

    def test_pdf_and_docx_extraction_collect_text_keywords_and_preview(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            pdf_path = _write(
                Path(tmp_dir) / "drawing.pdf",
                tasks._simple_pdf_bytes(
                    "TITLE BLOCK",
                    ["REV A", "MATERIAL: STEEL", "TOL +/-0.1", "PROCESS CNC"],
                ),
            )
            docx_path = _write(Path(tmp_dir) / "notes.docx", _simple_docx_bytes("REV B MATERIAL ABS TOL +/-0.2 CNC"))

            pdf_result = extract_format_intelligence(
                pdf_path,
                file_id="scx_file_eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
                tenant_id=7,
                original_filename="drawing.pdf",
                mime_type="application/pdf",
                size_bytes=pdf_path.stat().st_size,
            )
            docx_result = extract_format_intelligence(
                docx_path,
                file_id="scx_file_ffffffff-ffff-ffff-ffff-ffffffffffff",
                tenant_id=7,
                original_filename="notes.docx",
                mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                size_bytes=docx_path.stat().st_size,
            )

        self.assertEqual(pdf_result["page_count"], 1)
        self.assertIn("material", pdf_result["detected_keywords"])
        self.assertIn("STEEL", " ".join(pdf_result["material_mentions"]))
        self.assertIn("CNC", " ".join(pdf_result["process_mentions"]).upper())
        self.assertIn("REV A", pdf_result["extracted_text_preview"])

        self.assertEqual(docx_result["extraction_status"], "completed")
        self.assertIn("REV B", docx_result["extracted_text_preview"])
        self.assertIn("ABS", " ".join(docx_result["material_mentions"]))
        self.assertIn("CNC", " ".join(docx_result["process_mentions"]).upper())

    def test_supported_format_fails_closed_on_mime_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = _write(Path(tmp_dir) / "part.stl", _cube_ascii_stl())
            result = extract_format_intelligence(
                path,
                file_id="scx_file_11111111-2222-3333-4444-555555555555",
                tenant_id=7,
                original_filename="part.stl",
                mime_type="image/png",
                size_bytes=path.stat().st_size,
            )

        self.assertEqual(result["extraction_status"], "failed")
        self.assertEqual(result["extraction_errors"][0]["code"], "FORMAT_CONFLICT")
        self.assertNotIn("uploads/", json.dumps(result, ensure_ascii=True))

    def test_stage_convert_persists_extraction_result_for_supported_mesh(self) -> None:
        row = SimpleNamespace(
            file_id="scx_file_12121212-1212-1212-1212-121212121212",
            tenant_id=7,
            bucket="private-bucket",
            object_key="uploads/tenant_7/private/original",
            original_filename="part.stl",
            content_type="model/stl",
            size_bytes=len(_cube_ascii_stl()),
            sha256=None,
            status="queued",
            meta={"project_id": "default"},
            gltf_key=None,
            thumbnail_key=None,
            folder_key=None,
        )
        db = _FakeDb(row)
        s3 = _FakeS3(_cube_ascii_stl())
        envelope = EventEnvelope.build(
            event_type="file.uploaded",
            source="test",
            subject=row.file_id,
            tenant_id="7",
            project_id="default",
            data={"file_id": row.file_id, "version_no": 1},
        )

        with patch.object(tasks, "get_s3_client", return_value=s3), \
             patch.object(tasks, "load_rule_config_map", return_value=_rules()), \
             patch.object(tasks, "upsert_projection", return_value=None):
            result = tasks._stage_convert(db, envelope, 1)

        extraction = row.meta["extraction_result"]
        self.assertEqual(result["file_id"], row.file_id)
        self.assertEqual(extraction["extraction_status"], "completed")
        self.assertEqual(extraction["support_tier"], "dfm_supported")
        self.assertTrue(extraction["geometry_extracted"])
        self.assertEqual(row.meta["geometry_meta_json"]["triangle_count"], 12)
        self.assertTrue(any(key.endswith("/assembly_meta.json") for _bucket, key, _body, _ctype in s3.puts))

    def test_stage_convert_fails_closed_for_corrupt_supported_pdf(self) -> None:
        row = SimpleNamespace(
            file_id="scx_file_34343434-3434-3434-3434-343434343434",
            tenant_id=7,
            bucket="private-bucket",
            object_key="uploads/tenant_7/private/original",
            original_filename="drawing.pdf",
            content_type="application/pdf",
            size_bytes=11,
            sha256=None,
            status="queued",
            meta={"project_id": "default"},
            gltf_key=None,
            thumbnail_key=None,
            folder_key=None,
        )
        db = _FakeDb(row)
        s3 = _FakeS3(b"not-a-pdf")
        envelope = EventEnvelope.build(
            event_type="file.uploaded",
            source="test",
            subject=row.file_id,
            tenant_id="7",
            project_id="default",
            data={"file_id": row.file_id, "version_no": 1},
        )

        with patch.object(tasks, "get_s3_client", return_value=s3), \
             patch.object(tasks, "load_rule_config_map", return_value=_rules()), \
             patch.object(tasks, "upsert_projection", return_value=None):
            with self.assertRaises(tasks.PermanentStageError):
                tasks._stage_convert(db, envelope, 1)

        extraction = row.meta["extraction_result"]
        self.assertEqual(extraction["extraction_status"], "failed")
        self.assertEqual(extraction["extraction_errors"][0]["code"], "FORMAT_SIGNATURE_MISMATCH")
        self.assertNotIn("private-bucket", json.dumps(extraction, ensure_ascii=True))
        self.assertNotIn("uploads/", json.dumps(extraction, ensure_ascii=True))


if __name__ == "__main__":
    unittest.main()
