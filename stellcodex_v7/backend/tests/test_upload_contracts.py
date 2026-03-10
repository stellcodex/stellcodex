from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi import FastAPI

from app.api.v1.routes import product as product_routes
from app.api.v1.routes import files as files_routes
from app.api.v1.routes.files import router as files_router
from app.api.v1.routes.product import router as product_router
from app.db import get_db as app_get_db
from app.db.session import get_db as session_get_db
from app.security.deps import Principal, get_current_principal


def _guest(owner_sub: str = "guest-1") -> Principal:
    return Principal(typ="guest", owner_sub=owner_sub, anon=True)


def _valid_assembly_meta() -> dict:
    return {
        "occurrences": [
            {
                "occurrence_id": "occ_001",
                "part_id": "part_001",
                "display_name": "Bracket",
                "selectable": True,
                "children": [],
            }
        ],
        "index": {
            "occurrence_id_to_gltf_nodes": {
                "occ_001": ["node_1"],
            }
        },
    }


def _file_row(**overrides):
    payload = {
        "file_id": "scx_file_11111111-1111-1111-1111-111111111111",
        "owner_sub": "guest-1",
        "owner_anon_sub": "guest-1",
        "owner_user_id": None,
        "bucket": "private-bucket",
        "object_key": "uploads/tenant_1/secret/original",
        "original_filename": "demo.step",
        "content_type": "application/step",
        "size_bytes": 12345,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "status": "ready",
        "visibility": "private",
        "thumbnail_key": "thumbs/internal-preview.png",
        "gltf_key": "lod/private-lod0.glb",
        "meta": {
            "kind": "3d",
            "mode": "brep",
            "assembly_meta_key": "metadata/secret/assembly.json",
            "assembly_meta": _valid_assembly_meta(),
            "preview_jpg_keys": [
                "previews/private_0.jpg",
                "previews/private_1.jpg",
                "previews/private_2.jpg",
            ],
            "lods": {
                "lod0": {"key": "lod/private-lod0.glb", "ready": True},
                "lod1": {"key": "lod/private-lod1.glb", "ready": True},
            },
        },
    }
    payload.update(overrides)
    return SimpleNamespace(**payload)


def _assert_no_private_fields(payload: dict) -> None:
    text = json.dumps(payload, ensure_ascii=True, default=str).lower()
    for banned in ("storage_key", "object_key", "revision_id", "s3://", "r2://", "\"bucket\""):
        if banned in text:
            raise AssertionError(f"public payload leaked banned token: {banned}")


def _assert_safe_error_payload(status_code: int, headers: dict[str, str], body: bytes) -> None:
    text = body.decode("utf-8", errors="replace")
    if status_code not in {400, 401, 403, 404, 409, 413, 415, 422, 429}:
        raise AssertionError(f"unexpected unsafe status code: {status_code}")
    if "application/json" not in headers.get("content-type", ""):
        raise AssertionError(f"unexpected content-type: {headers.get('content-type')}")
    for banned in ("Traceback", "<html", "/root/workspace", "private-bucket", "uploads/", "object_key", "storage_key"):
        if banned in text:
            raise AssertionError(f"unsafe error payload leaked: {banned}")


def _multipart_contract_app() -> FastAPI:
    app = FastAPI()
    app.include_router(files_router, prefix="/api/v1/files")
    app.include_router(product_router, prefix="/api/v1")

    def _fake_db():
        yield object()

    principal = Principal(typ="guest", owner_sub="guest-1", anon=True)
    app.dependency_overrides[session_get_db] = _fake_db
    app.dependency_overrides[app_get_db] = _fake_db
    app.dependency_overrides[files_routes._require_principal] = lambda: principal
    app.dependency_overrides[get_current_principal] = lambda: principal
    return app


def _dispatch_asgi(app: FastAPI, method: str, path: str, *, headers: dict[str, str] | None = None, body: bytes = b"") -> tuple[int, dict[str, str], bytes]:
    sent: list[dict] = []
    header_items = []
    for key, value in (headers or {}).items():
        header_items.append((key.lower().encode("latin-1"), value.encode("latin-1")))

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method.upper(),
        "scheme": "http",
        "path": path,
        "raw_path": path.encode("ascii"),
        "query_string": b"",
        "headers": header_items,
        "client": ("127.0.0.1", 50000),
        "server": ("testserver", 80),
        "root_path": "",
    }
    messages = [{"type": "http.request", "body": body, "more_body": False}]

    async def receive():
        if messages:
            return messages.pop(0)
        return {"type": "http.disconnect"}

    async def send(message):
        sent.append(message)

    asyncio.run(app(scope, receive, send))
    start = next(message for message in sent if message["type"] == "http.response.start")
    body_parts = [message.get("body", b"") for message in sent if message["type"] == "http.response.body"]
    response_headers = {
        key.decode("latin-1"): value.decode("latin-1")
        for key, value in start.get("headers", [])
    }
    return int(start["status"]), response_headers, b"".join(body_parts)


class UploadContractsTests(unittest.TestCase):
    def test_canonical_upload_route_exists(self) -> None:
        paths = {route.path for route in files_router.routes}
        self.assertIn("/upload", paths)
        self.assertIn("/{file_id}", paths)
        self.assertIn("/{file_id}/status", paths)

    def test_legacy_upload_alias_exists(self) -> None:
        paths = {route.path for route in product_router.routes}
        self.assertIn("/upload", paths)

    def test_canonical_and_legacy_upload_routes_share_same_public_response_model(self) -> None:
        canonical = next(route for route in files_router.routes if route.path == "/upload")
        legacy = next(route for route in product_router.routes if route.path == "/upload")
        self.assertIs(canonical.response_model, files_routes.FileOut)
        self.assertIs(legacy.response_model, files_routes.FileOut)
        self.assertIn("file_id", files_routes.FileOut.model_fields)

    def test_initiate_upload_returns_public_safe_ingress_url(self) -> None:
        class FakeDB:
            def __init__(self) -> None:
                self.rows = []

            def add(self, row) -> None:
                self.rows.append(row)

            def commit(self) -> None:
                return None

            def refresh(self, row) -> None:
                row.file_id = "scx_file_22222222-2222-2222-2222-222222222222"
                return None

        db = FakeDB()
        payload = files_routes.InitiateIn(filename="demo.step", content_type="application/step", size_bytes=64)

        with patch.object(files_routes, "resolve_or_create_tenant_id", return_value=7), \
             patch.object(files_routes, "upsert_projection", return_value=None):
            result = files_routes.initiate_upload(payload, db=db, principal=_guest())

        body = result.model_dump()
        self.assertEqual(body["file_id"], db.rows[0].file_id)
        self.assertEqual(body["upload_url"], f"/api/v1/files/{body['file_id']}/content")
        self.assertEqual(body["expires_in_seconds"], 900)
        _assert_no_private_fields(body)
        self.assertNotIn("http://", body["upload_url"])
        self.assertNotIn("https://", body["upload_url"])
        self.assertNotIn("uploads/", body["upload_url"])

    def test_upload_validation_rejects_unsupported_and_mismatched_types(self) -> None:
        cases = [
            ("malware.exe", "application/octet-stream"),
            ("demo.step", "image/png"),
            ("demo.step.exe", "application/octet-stream"),
        ]
        for filename, content_type in cases:
            with self.subTest(filename=filename, content_type=content_type):
                with self.assertRaises(HTTPException) as ctx:
                    files_routes._validate_upload(content_type, 64, filename)
                self.assertEqual(ctx.exception.status_code, 415)

    def test_upload_validation_rejects_empty_and_oversize_uploads(self) -> None:
        with self.assertRaises(HTTPException) as empty_ctx:
            files_routes._validate_upload("application/step", 0, "demo.step")
        self.assertEqual(empty_ctx.exception.status_code, 400)
        self.assertEqual(empty_ctx.exception.detail, "Empty file")

        with patch.object(files_routes.settings, "max_upload_bytes", 8):
            with self.assertRaises(HTTPException) as oversize_ctx:
                files_routes._validate_upload("application/step", 9, "demo.step")
        self.assertEqual(oversize_ctx.exception.status_code, 413)

    def test_serialize_file_out_ready_uses_public_file_id_urls_only(self) -> None:
        file_row = _file_row()

        payload = files_routes._serialize_file_out(file_row).model_dump()

        self.assertEqual(payload["file_id"], file_row.file_id)
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["gltf_url"], f"/api/v1/files/{file_row.file_id}/gltf")
        self.assertEqual(
            payload["preview_urls"],
            [
                f"/api/v1/files/{file_row.file_id}/preview/0",
                f"/api/v1/files/{file_row.file_id}/preview/1",
                f"/api/v1/files/{file_row.file_id}/preview/2",
            ],
        )
        self.assertEqual(payload["thumbnail_url"], f"/api/v1/files/{file_row.file_id}/thumbnail")
        _assert_no_private_fields(payload)

    def test_serialize_file_out_downgrades_ready_without_assembly_meta(self) -> None:
        file_row = _file_row(
            meta={
                "kind": "3d",
                "mode": "brep",
                "preview_jpg_keys": ["a.jpg", "b.jpg", "c.jpg"],
            }
        )

        payload = files_routes._serialize_file_out(file_row).model_dump()

        self.assertEqual(payload["file_id"], file_row.file_id)
        self.assertEqual(payload["status"], "failed")
        self.assertEqual(payload["error_code"], "ASSEMBLY_META_MISSING")
        self.assertIsNone(payload["gltf_url"])
        self.assertIsNone(payload["preview_url"])
        self.assertIsNone(payload["preview_urls"])
        _assert_no_private_fields(payload)

    def test_serialize_file_out_doc_uses_public_pdf_route_only(self) -> None:
        file_row = _file_row(
            original_filename="sheet.pdf",
            content_type="application/pdf",
            gltf_key=None,
            thumbnail_key="thumbs/public-preview.png",
            meta={"kind": "doc", "mode": "visual_only", "pdf_key": "private/reports/a.pdf"},
        )

        payload = files_routes._serialize_file_out(file_row).model_dump()

        self.assertEqual(payload["file_id"], file_row.file_id)
        self.assertEqual(payload["preview_url"], f"/api/v1/files/{file_row.file_id}/pdf")
        self.assertEqual(payload["original_url"], f"/api/v1/files/{file_row.file_id}/pdf")
        self.assertIsNone(payload["gltf_url"])
        _assert_no_private_fields(payload)

    def test_file_status_rejects_invalid_file_id(self) -> None:
        with self.assertRaises(HTTPException) as ctx:
            files_routes.file_status("not-a-file-id", db=object(), principal=_guest())
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(ctx.exception.detail, "Invalid file id")

    def test_file_status_forbids_guest_without_ownership(self) -> None:
        file_row = _file_row(owner_sub="guest-2", owner_anon_sub="guest-2")

        with patch.object(files_routes, "_get_file_by_identifier", return_value=file_row):
            with self.assertRaises(HTTPException) as ctx:
                files_routes.file_status(file_row.file_id, db=object(), principal=_guest("guest-1"))

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertEqual(ctx.exception.detail, "Forbidden")

    def test_file_status_uses_projection_progress_and_public_derivatives(self) -> None:
        file_row = _file_row()
        projection = SimpleNamespace(
            status="ready",
            stage_progress=88,
            payload_json={"progress": "assembly complete", "stage": "pack"},
            timestamps={},
        )

        with patch.object(files_routes, "_get_file_by_identifier", return_value=file_row):
            with patch.object(files_routes, "get_projection", return_value=projection):
                result = files_routes.file_status(file_row.file_id, db=object(), principal=_guest())

        self.assertEqual(result.file_id, file_row.file_id)
        self.assertEqual(result.state, "succeeded")
        self.assertEqual(result.progress_hint, "assembly complete")
        self.assertEqual(result.progress_percent, 88)
        self.assertEqual(result.stage, "pack")
        self.assertEqual(result.derivatives_available, ["gltf", "thumbnail", "preview_jpg", "assembly_meta"])

    def test_file_status_surfaces_safe_extraction_status(self) -> None:
        file_row = _file_row(
            meta={
                "kind": "3d",
                "mode": "mesh_approx",
                "assembly_meta_key": "metadata/secret/assembly.json",
                "assembly_meta": _valid_assembly_meta(),
                "preview_jpg_keys": ["p0.jpg", "p1.jpg", "p2.jpg"],
                "extraction_result": {
                    "source_format": "stl",
                    "support_tier": "dfm_supported",
                    "extraction_status": "completed",
                    "extraction_stage": "completed",
                    "preview_supported": True,
                    "metadata_extracted": True,
                    "geometry_extracted": True,
                    "dfm_supported": True,
                    "bbox": {"x": 10.0, "y": 20.0, "z": 30.0},
                },
            }
        )

        with patch.object(files_routes, "_get_file_by_identifier", return_value=file_row), \
             patch.object(files_routes, "get_projection", return_value=None):
            result = files_routes.file_status(file_row.file_id, db=object(), principal=_guest())

        self.assertEqual(result.extraction_status, "completed")
        self.assertEqual(result.extraction_stage, "completed")
        self.assertEqual(result.support_tier, "dfm_supported")

    def test_file_detail_uses_public_file_id_and_public_lods_only(self) -> None:
        file_row = _file_row()

        with patch.object(files_routes, "_get_file_by_identifier", return_value=file_row), \
             patch.object(files_routes, "get_projection", return_value=None), \
             patch.object(files_routes, "_persist_ready_contract_failure", return_value=False):
            payload = files_routes.get_file(file_row.file_id, db=object(), principal=_guest()).model_dump()

        self.assertEqual(payload["file_id"], file_row.file_id)
        self.assertEqual(payload["lods"]["lod0"]["url"], f"/api/v1/files/{file_row.file_id}/lod/lod0")
        self.assertEqual(payload["lods"]["lod1"]["url"], f"/api/v1/files/{file_row.file_id}/lod/lod1")
        self.assertNotIn("key", payload["lods"]["lod0"])
        self.assertNotIn("key", payload["lods"]["lod1"])
        _assert_no_private_fields(payload)

    def test_file_detail_includes_safe_extraction_summary(self) -> None:
        file_row = _file_row(
            meta={
                "kind": "doc",
                "mode": "doc",
                "pdf_key": "private/reports/a.pdf",
                "extraction_result": {
                    "source_format": "pdf",
                    "media_class": "document",
                    "support_tier": "dfm_supported",
                    "extraction_status": "completed",
                    "extraction_stage": "completed",
                    "preview_supported": True,
                    "metadata_extracted": True,
                    "geometry_extracted": False,
                    "dfm_supported": True,
                    "page_count": 2,
                    "extracted_text_preview": "REV B MATERIAL: STEEL TOLERANCE +/-0.1",
                    "material_mentions": ["STEEL"],
                    "revision_mentions": ["REV B"],
                    "engineering_rules": [{"rule_id": "tolerance_mention_missing", "status": "warn"}],
                    "object_key": "uploads/private/hidden.pdf",
                },
            },
            original_filename="sheet.pdf",
            content_type="application/pdf",
            gltf_key=None,
            thumbnail_key="thumbs/public-preview.png",
        )

        with patch.object(files_routes, "_get_file_by_identifier", return_value=file_row), \
             patch.object(files_routes, "get_projection", return_value=None), \
             patch.object(files_routes, "_persist_ready_contract_failure", return_value=False):
            payload = files_routes.get_file(file_row.file_id, db=object(), principal=_guest()).model_dump()

        summary = payload["extraction_summary"]
        self.assertEqual(summary["support_tier"], "dfm_supported")
        self.assertEqual(summary["page_count"], 2)
        self.assertIn("REV B", summary["extracted_text_preview"])
        self.assertNotIn("object_key", json.dumps(summary, ensure_ascii=True))
        _assert_no_private_fields(payload)

    def test_cross_tenant_detail_and_manifest_access_fail(self) -> None:
        file_row = _file_row(owner_sub="guest-2", owner_anon_sub="guest-2")

        with patch.object(files_routes, "_get_file_by_identifier", return_value=file_row):
            with self.assertRaises(HTTPException) as detail_ctx:
                files_routes.get_file(file_row.file_id, db=object(), principal=_guest("guest-1"))
        self.assertEqual(detail_ctx.exception.status_code, 403)

        with patch.object(files_routes, "_get_file_by_identifier", return_value=file_row):
            with self.assertRaises(HTTPException) as manifest_ctx:
                files_routes.file_manifest(file_row.file_id, db=object(), principal=_guest("guest-1"))
        self.assertEqual(manifest_ctx.exception.status_code, 403)

    def test_manifest_uses_public_model_id_and_asset_paths_without_internal_keys(self) -> None:
        file_row = _file_row()

        with patch.object(files_routes, "_get_file_by_identifier", return_value=file_row):
            manifest = files_routes.file_manifest(file_row.file_id, db=object(), principal=_guest())

        self.assertEqual(manifest["model_id"], file_row.file_id)
        self.assertEqual(
            manifest["lod"],
            {
                "lod0": "assets/lod/lod0.glb",
                "lod1": "assets/lod/lod1.glb",
            },
        )
        manifest_text = json.dumps(manifest, ensure_ascii=True)
        self.assertNotIn("private-lod0.glb", manifest_text)
        self.assertNotIn("private-lod1.glb", manifest_text)
        self.assertNotIn("assembly_meta_key", manifest_text)

    def test_file_decision_json_builds_and_persists_public_contract(self) -> None:
        file_row = _file_row(decision_json=None, meta={"kind": "3d"})
        decision_json = {
            "state": "S4",
            "state_label": "review_required",
            "status_gate": "BLOCKED",
            "approval_required": True,
            "rule_version": "v7.2.0",
            "mode": "manufacturing_review",
            "confidence": 0.81,
            "manufacturing_method": "cnc",
            "rule_explanations": ["thin wall risk"],
            "conflict_flags": ["wall_thickness_conflict"],
            "risk_flags": ["thin_wall"],
        }

        class FakeDB:
            def __init__(self) -> None:
                self.added = []
                self.commits = 0

            def add(self, obj) -> None:
                self.added.append(obj)

            def commit(self) -> None:
                self.commits += 1

        db = FakeDB()

        with patch.object(files_routes, "_get_file_by_identifier", return_value=file_row), \
             patch.object(files_routes, "load_rule_config_map", return_value={}), \
             patch.object(files_routes, "build_decision_json", return_value=decision_json) as build_mock, \
             patch.object(files_routes, "normalize_decision_json", side_effect=lambda _f, _rules, payload: payload), \
             patch.object(files_routes, "upsert_orchestrator_session") as session_mock, \
             patch.object(files_routes, "upsert_projection") as projection_mock:
            result = files_routes.file_decision_json(file_row.file_id, db=db, principal=_guest())

        payload = result.model_dump()
        self.assertEqual(payload["file_id"], file_row.file_id)
        self.assertEqual(payload["state"], "S4")
        self.assertEqual(payload["state_code"], "S4")
        self.assertTrue(payload["approval_required"])
        self.assertEqual(payload["decision_json"], decision_json)
        _assert_no_private_fields(payload)
        self.assertEqual(file_row.decision_json, decision_json)
        self.assertEqual(file_row.meta["decision_json"], decision_json)
        self.assertEqual(db.added, [file_row])
        self.assertEqual(db.commits, 1)
        build_mock.assert_called_once()
        session_mock.assert_called_once_with(db, file_row, decision_json)
        projection_mock.assert_called_once_with(db, file_row)

    def test_download_url_does_not_expose_bucket_or_object_key(self) -> None:
        file_row = _file_row()

        with patch.object(files_routes, "_get_file_by_identifier", return_value=file_row):
            result = files_routes.download_url(file_row.file_id, db=object(), principal=_guest())

        payload = result.model_dump()
        self.assertEqual(payload["url"], f"/api/v1/files/{file_row.file_id}/content?download=1")
        self.assertEqual(payload["expires_in_seconds"], 900)
        self.assertNotIn(file_row.bucket, payload["url"])
        self.assertNotIn(file_row.object_key, payload["url"])

    def test_upload_content_ingress_stays_file_id_based_and_no_leak(self) -> None:
        file_row = _file_row(status="pending")

        class FakeRequest:
            headers = {"content-type": "application/step"}

            async def stream(self):
                yield b"ISO-10303-21;"

        class FakeS3Client:
            def __init__(self) -> None:
                self.calls = []

            def upload_fileobj(self, stream, bucket, key, ExtraArgs):
                self.calls.append((stream.read(), bucket, key, ExtraArgs))

        class FakeDB:
            def __init__(self) -> None:
                self.added = []
                self.commits = 0

            def add(self, row) -> None:
                self.added.append(row)

            def commit(self) -> None:
                self.commits += 1

        fake_s3 = FakeS3Client()
        db = FakeDB()
        with patch.object(files_routes, "_get_file_by_identifier", return_value=file_row), \
             patch.object(files_routes, "s3_client", return_value=fake_s3):
            response = asyncio.run(
                files_routes.upload_content(file_row.file_id, request=FakeRequest(), db=db, principal=_guest())
            )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(db.commits, 1)
        self.assertEqual(len(fake_s3.calls), 1)
        payload_bytes, bucket, key, extra_args = fake_s3.calls[0]
        self.assertEqual(payload_bytes, b"ISO-10303-21;")
        self.assertEqual(bucket, file_row.bucket)
        self.assertEqual(key, file_row.object_key)
        self.assertEqual(extra_args["ContentType"], file_row.content_type)
        self.assertFalse(response.body)

    def test_malformed_multipart_boundary_returns_safe_json_error(self) -> None:
        app = _multipart_contract_app()
        status_code, headers, body = _dispatch_asgi(
            app,
            "POST",
            "/api/v1/files/upload",
            headers={"content-type": "multipart/form-data; boundary=bad"},
            body=b"--bad\r\nContent-Disposition: form-data; name=\"upload\"; filename=\"demo.step\"\r\nContent-Type: application/step\r\n\r\nbroken",
        )

        self.assertEqual(status_code, 422)
        _assert_safe_error_payload(status_code, headers, body)

    def test_missing_file_part_and_empty_multipart_body_return_safe_json_errors(self) -> None:
        app = _multipart_contract_app()
        cases = [
            ("POST", "/api/v1/files/upload", {"content-type": "multipart/form-data; boundary=empty"}, b""),
            ("POST", "/api/v1/upload", {"content-type": "multipart/form-data; boundary=empty"}, b""),
            ("POST", "/api/v1/upload", {}, b"project_id=x"),
        ]

        for method, path, headers, body in cases:
            with self.subTest(path=path, headers=headers):
                status_code, response_headers, response_body = _dispatch_asgi(
                    app, method, path, headers=headers, body=body
                )
                self.assertEqual(status_code, 422)
                _assert_safe_error_payload(status_code, response_headers, response_body)

    def test_broken_content_disposition_and_invalid_mixed_payload_fail_safely(self) -> None:
        app = _multipart_contract_app()
        bad_body = (
            b"--mix\r\n"
            b"Content-Disposition: form-data; name=\"upload\"\r\n"
            b"Content-Type: application/step\r\n\r\n"
            b"ISO-10303-21;\r\n"
            b"--mix--\r\n"
        )
        status_code, headers, body = _dispatch_asgi(
            app,
            "POST",
            "/api/v1/files/upload",
            headers={"content-type": "multipart/form-data; boundary=mix"},
            body=bad_body,
        )

        self.assertEqual(status_code, 422)
        _assert_safe_error_payload(status_code, headers, body)

    def test_download_content_download_mode_sets_attachment_header(self) -> None:
        file_row = _file_row()

        class FakeBody:
            def iter_chunks(self):
                return iter([b"cad-bytes"])

        class FakeS3Client:
            def get_object(self, **_kwargs):
                return {"Body": FakeBody()}

        with patch.object(files_routes, "_get_file_by_identifier", return_value=file_row), \
             patch.object(files_routes, "s3_client", return_value=FakeS3Client()):
            response = files_routes.download_content(
                file_row.file_id,
                download=True,
                db=object(),
                principal=_guest(),
            )

        self.assertEqual(response.headers["content-disposition"], 'attachment; filename="demo.step"')
        self.assertNotIn(file_row.bucket, response.headers["content-disposition"])
        self.assertNotIn(file_row.object_key, response.headers["content-disposition"])

    def test_safe_object_key_sanitizes_path_traversal_and_replay_uploads_stay_isolated(self) -> None:
        first = files_routes._safe_object_key(tenant_id=7, owner_sub="../../escape")
        second = files_routes._safe_object_key(tenant_id=7, owner_sub="../../escape")

        self.assertTrue(first.startswith("uploads/tenant_7/"))
        self.assertTrue(second.startswith("uploads/tenant_7/"))
        self.assertNotIn("../", first)
        self.assertNotIn("..\\", first)
        self.assertNotEqual(first, second)

    def test_download_content_forbidden_and_not_ready_paths_fail_closed(self) -> None:
        forbidden_row = _file_row(owner_sub="guest-2", owner_anon_sub="guest-2")
        not_ready_row = _file_row(status="processing")

        with patch.object(files_routes, "_get_file_by_identifier", return_value=forbidden_row):
            with self.assertRaises(HTTPException) as forbidden_ctx:
                files_routes.download_content(forbidden_row.file_id, db=object(), principal=_guest("guest-1"))
        self.assertEqual(forbidden_ctx.exception.status_code, 403)

        with patch.object(files_routes, "_get_file_by_identifier", return_value=not_ready_row):
            with self.assertRaises(HTTPException) as not_ready_ctx:
                files_routes.download_content(not_ready_row.file_id, db=object(), principal=_guest())
        self.assertEqual(not_ready_ctx.exception.status_code, 409)
        self.assertEqual(not_ready_ctx.exception.detail, "File not ready")

    def test_thumbnail_and_preview_stream_without_storage_headers(self) -> None:
        file_row = _file_row()

        class FakeBody:
            def iter_chunks(self):
                return iter([b"preview"])

        class FakeS3Client:
            def get_object(self, **_kwargs):
                return {"Body": FakeBody()}

        with patch.object(files_routes, "_get_file_by_identifier", return_value=file_row), \
             patch.object(files_routes, "s3_client", return_value=FakeS3Client()):
            thumb = files_routes.download_thumbnail(file_row.file_id, db=object(), principal=_guest())
            preview = files_routes.download_preview_jpg(file_row.file_id, 0, db=object(), principal=_guest())

        self.assertEqual(thumb.media_type, "image/png")
        self.assertEqual(preview.media_type, "image/jpeg")
        thumb_headers = json.dumps(dict(thumb.headers), ensure_ascii=True)
        preview_headers = json.dumps(dict(preview.headers), ensure_ascii=True)
        self.assertNotIn(file_row.bucket, thumb_headers)
        self.assertNotIn(file_row.object_key, thumb_headers)
        self.assertNotIn(file_row.bucket, preview_headers)
        self.assertNotIn(file_row.object_key, preview_headers)


if __name__ == "__main__":
    unittest.main()
