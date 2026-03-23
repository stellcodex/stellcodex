from __future__ import annotations

import asyncio
import io
import uuid
import unittest
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterator, List, Optional, Tuple
from unittest import mock

from fastapi import HTTPException
from starlette.datastructures import Headers, UploadFile as StarletteUploadFile
from starlette.requests import Request
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

import app.models  # noqa: F401
from app.api.v1.routes import admin as admin_routes
from app.api.v1.routes import approvals as approval_routes
from app.api.v1.routes import files as file_routes
from app.api.v1.routes import jobs as job_routes
from app.api.v1.routes import orchestrator as orchestrator_routes
from app.api.v1.routes import platform_contract as platform_contract_routes
from app.api.v1.routes import product as product_routes
from app.api.v1.routes import share as share_routes
from app.core.config import settings
from app.core.ids import format_scx_file_id
from app.db.base import Base
from app.models.audit import AuditEvent
from app.models.file import UploadFile as UploadFileModel
from app.models.file_version import FileVersion
from app.models.job_failure import JobFailure
from app.models.orchestrator import OrchestratorSession
from app.models.share import Share
from app.models.tenant import Tenant
from app.security.deps import Principal


def build_decision_json(*, mode: str | None, rule_version: str) -> dict:
    normalized_mode = "brep" if mode == "brep" else "mesh_approx" if mode == "mesh_approx" else "visual_only"
    return {
        "rule_version": rule_version,
        "mode": normalized_mode,
        "confidence": 0.0,
        "manufacturing_method": "unknown",
        "rule_explanations": [
            {
                "rule_id": "R00_DEFAULT",
                "triggered": False,
                "severity": "INFO",
                "reference": "rule_configs:default",
                "reasoning": "Deterministic decision completed without blocking findings.",
            }
        ],
        "conflict_flags": [],
    }


def apply_session_state(session: OrchestratorSession, *, state: str, decision_json: dict) -> None:
    state_code = str(state).split(" ", 1)[0].strip().upper()
    session.state = state_code
    session.state_code = state_code
    session.state_label = state_code
    session.approval_required = bool(decision_json.get("conflict_flags"))
    session.status_gate = "NEEDS_APPROVAL" if session.approval_required else "PASS"
    session.risk_flags = decision_json.get("conflict_flags") if isinstance(decision_json.get("conflict_flags"), list) else []


class _DummyQueue:
    def __init__(self, count: int) -> None:
        self.count = count


class _DummyS3:
    def __init__(self) -> None:
        self.uploads: List[Tuple[str, str, bytes]] = []

    def head_bucket(self, Bucket: str) -> None:  # noqa: N803
        return None

    def upload_fileobj(self, fileobj, bucket: str, key: str, ExtraArgs=None) -> None:  # noqa: N803
        fileobj.seek(0)
        self.uploads.append((bucket, key, fileobj.read()))
        fileobj.seek(0)


class BackendCoreClosureContractTests(unittest.TestCase):
    member_uuid = uuid.UUID("00000000-0000-0000-0000-000000000111")
    other_uuid = uuid.UUID("00000000-0000-0000-0000-000000000222")
    admin_uuid = uuid.UUID("00000000-0000-0000-0000-000000000333")
    current_principal = Principal(typ="user", user_id=str(member_uuid), role="member")

    @classmethod
    def setUpClass(cls) -> None:
        cls.schema_name = f"test_backend_core_{uuid.uuid4().hex[:12]}"
        cls.admin_engine = create_engine(settings.DATABASE_URL)
        with cls.admin_engine.begin() as conn:
            conn.execute(text(f"CREATE SCHEMA {cls.schema_name}"))

        cls.engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"options": f"-csearch_path={cls.schema_name}"},
        )
        Base.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(bind=cls.engine, autocommit=False, autoflush=False)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()
        with cls.admin_engine.begin() as conn:
            conn.execute(text(f"DROP SCHEMA IF EXISTS {cls.schema_name} CASCADE"))
        cls.admin_engine.dispose()

    def setUp(self) -> None:
        self._truncate_all()
        type(self).current_principal = Principal(typ="user", user_id=str(self.member_uuid), role="member")
        self.tenant_id = self._create_tenant()

    def _truncate_all(self) -> None:
        table_names = ", ".join(f'"{table.name}"' for table in reversed(Base.metadata.sorted_tables))
        with self.SessionLocal.begin() as db:
            db.execute(text(f"TRUNCATE TABLE {table_names} RESTART IDENTITY CASCADE"))

    @contextmanager
    def _db(self) -> Iterator[Session]:
        db = self.SessionLocal()
        try:
            yield db
            db.commit()
        finally:
            db.close()

    def _create_tenant(self) -> int:
        with self._db() as db:
            tenant = Tenant(code=f"tenant-{uuid.uuid4().hex[:8]}", name="Test Tenant")
            db.add(tenant)
            db.flush()
            return int(tenant.id)

    def _public_file_id(self, stored_file_id: str) -> str:
        return format_scx_file_id(stored_file_id)

    def _base_meta(self, *, kind: str, mode: str, ready_contract: bool) -> dict:
        payload = {
            "project_id": "default",
            "kind": kind,
            "mode": mode,
            "rule_version": "v1.0",
        }
        if ready_contract and kind == "3d":
            payload.update(
                {
                    "assembly_meta_key": "assemblies/current.json",
                    "preview_jpg_keys": ["preview/0.jpg", "preview/1.jpg", "preview/2.jpg"],
                    "geometry_meta_json": {"part_count": 3},
                }
            )
        return payload

    def _seed_file(
        self,
        *,
        stored_file_id: Optional[str] = None,
        owner_user_id: Optional[uuid.UUID] = None,
        original_filename: str = "part.step",
        content_type: str = "application/octet-stream",
        status: str = "ready",
        kind: str = "3d",
        mode: str = "brep",
        ready_contract: bool = True,
        meta: Optional[Dict] = None,
        decision_json: Optional[Dict] = None,
    ) -> str:
        file_id = stored_file_id or format_scx_file_id(uuid.uuid4())
        owner = owner_user_id or self.member_uuid
        meta_payload = self._base_meta(kind=kind, mode=mode, ready_contract=ready_contract)
        if meta:
            meta_payload.update(meta)
        stored_decision = decision_json if decision_json is not None else (meta_payload.get("decision_json") or {})
        with self._db() as db:
            row = UploadFileModel(
                file_id=file_id,
                owner_sub=f"user:{owner}",
                tenant_id=self.tenant_id,
                owner_user_id=owner,
                owner_anon_sub=None,
                is_anonymous=False,
                privacy="private",
                bucket="stellcodex-test",
                object_key=f"uploads/{file_id}/original",
                original_filename=original_filename,
                content_type=content_type,
                size_bytes=2048,
                sha256=None,
                gltf_key=f"glb/{file_id}.glb" if ready_contract and kind == "3d" else None,
                thumbnail_key=f"thumb/{file_id}.webp" if ready_contract else None,
                folder_key=f"project/default/{kind}/{mode}",
                meta=meta_payload,
                decision_json=stored_decision,
                status=status,
                visibility="private",
            )
            db.add(row)
        return str(file_id)

    def _seed_session(
        self,
        *,
        file_id: str,
        state: str,
        decision_json: Optional[Dict] = None,
        mode: str = "brep",
        rule_version: str = "v1.0",
    ) -> str:
        payload = decision_json or build_decision_json(mode=mode, rule_version=rule_version)
        with self._db() as db:
            session = OrchestratorSession(
                file_id=file_id,
                decision_json=payload,
                rule_version=rule_version,
                mode=mode,
                confidence=float(payload.get("confidence") or 0.0),
            )
            apply_session_state(session, state=state, decision_json=payload)
            db.add(session)
            db.flush()
            return str(session.id)

    def _seed_share(
        self,
        *,
        file_id: str,
        created_by_user_id: Optional[uuid.UUID] = None,
        token: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        revoked_at: Optional[datetime] = None,
    ) -> Tuple[str, str]:
        share_token = token or uuid.uuid4().hex
        with self._db() as db:
            share = Share(
                file_id=file_id,
                created_by_user_id=created_by_user_id or self.member_uuid,
                token=share_token,
                permission="view",
                expires_at=expires_at or (datetime.now(timezone.utc) + timedelta(hours=1)),
                revoked_at=revoked_at,
            )
            db.add(share)
            db.flush()
            return str(share.id), share.token

    def _seed_failure(self, *, file_id: str, stage: str = "convert", error_class: str = "RuntimeError") -> None:
        with self._db() as db:
            db.add(
                JobFailure(
                    job_id=f"job-{uuid.uuid4().hex[:8]}",
                    file_id=file_id,
                    stage=stage,
                    error_class=error_class,
                    message="backend failure summary",
                    traceback="traceback omitted",
                )
            )

    def _request(self, path: str) -> Request:
        scope = {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "path": path,
            "headers": [],
            "query_string": b"",
            "scheme": "http",
            "server": ("testserver", 80),
            "client": ("127.0.0.1", 12345),
        }
        return Request(scope)

    def test_recent_jobs_endpoint_returns_tenant_scoped_public_ids(self) -> None:
        legacy_file_id = str(uuid.uuid4())
        other_file_id = format_scx_file_id(uuid.uuid4())
        self._seed_file(stored_file_id=legacy_file_id, status="failed")
        self._seed_session(file_id=legacy_file_id, state="S4")
        self._seed_failure(file_id=legacy_file_id)
        self._seed_file(stored_file_id=other_file_id, owner_user_id=self.other_uuid, status="ready")

        with self._db() as db:
            payload = [item.model_dump() for item in job_routes.recent_jobs(limit=20, db=db, principal=self.current_principal)]
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["file_id"], self._public_file_id(legacy_file_id))
        self.assertEqual(payload[0]["error_code"], "CONVERT_RUNTIMEERROR")
        self.assertNotIn("object_key", payload[0])
        self.assertNotIn("bucket", payload[0])

    def test_versions_endpoint_lists_public_history_without_storage_keys(self) -> None:
        file_id = self._seed_file()

        with self._db() as db:
            payload = [item.model_dump() for item in file_routes.get_file_versions(file_id=file_id, db=db, principal=self.current_principal)]
        self.assertEqual(len(payload), 1)
        self.assertEqual(payload[0]["file_id"], file_id)
        self.assertEqual(payload[0]["version_number"], 1)
        self.assertTrue(payload[0]["is_current"])
        self.assertNotIn("bucket", payload[0])
        self.assertNotIn("object_key", payload[0])

    def test_new_version_preserves_file_id_and_creates_new_history(self) -> None:
        file_id = self._seed_file()
        with self._db() as db:
            first_versions = file_routes.get_file_versions(file_id=file_id, db=db, principal=self.current_principal)
        self.assertEqual(len(first_versions), 1)

        dummy_s3 = _DummyS3()
        file_bytes = b"ISO-10303-21;\nHEADER;\nENDSEC;\nEND-ISO-10303-21;\n"
        upload = StarletteUploadFile(
            filename="part-v2.step",
            file=io.BytesIO(file_bytes),
            headers=Headers({"content-type": "application/octet-stream"}),
        )
        with mock.patch("app.api.v1.routes.files.s3_client", return_value=dummy_s3), mock.patch(
            "app.workers.tasks.enqueue_convert_file",
            return_value="job-convert-v2",
        ):
            with self._db() as db:
                payload = asyncio.run(
                    file_routes.upload_new_version(
                        file_id=file_id,
                        upload=upload,
                        project_id=None,
                        projectId=None,
                        db=db,
                        principal=self.current_principal,
                    )
                ).model_dump()
        self.assertEqual(payload["file_id"], file_id)
        self.assertEqual(payload["status"], "queued")
        self.assertNotIn("object_key", payload)
        self.assertEqual(len(dummy_s3.uploads), 1)

        with self._db() as db:
            rows = (
                db.query(FileVersion)
                .filter(FileVersion.file_id == file_id)
                .order_by(FileVersion.version_number.asc())
                .all()
            )
            self.assertEqual([row.version_number for row in rows], [1, 2])
            self.assertFalse(rows[0].is_current)
            self.assertTrue(rows[1].is_current)
            file_row = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
            self.assertIsNotNone(file_row)
            self.assertEqual(file_row.file_id, file_id)
            self.assertEqual(file_row.original_filename, "part-v2.step")

    def test_orchestrator_decision_guarantees_non_blank_fallback(self) -> None:
        file_id = self._seed_file(ready_contract=False, meta={"decision_json": {}}, decision_json={})
        session_id = self._seed_session(file_id=file_id, state="S4", decision_json={})

        with self._db() as db:
            payload = orchestrator_routes.get_orchestrator_decision(
                session_id=session_id,
                db=db,
                principal=self.current_principal,
            ).model_dump()["decision_json"]
        self.assertIn("manufacturing_method", payload)
        self.assertIn("mode", payload)
        self.assertIn("confidence", payload)
        self.assertIn("rule_version", payload)
        self.assertTrue(payload["rule_explanations"])
        self.assertIn("decision_fallback_used", payload["conflict_flags"])

    def test_direct_upload_creates_session_and_queue_without_manual_start(self) -> None:
        dummy_s3 = _DummyS3()
        file_bytes = b"ISO-10303-21;\nHEADER;\nENDSEC;\nEND-ISO-10303-21;\n"
        upload = StarletteUploadFile(
            filename="auto-flow.step",
            file=io.BytesIO(file_bytes),
            headers=Headers({"content-type": "application/octet-stream"}),
        )

        with mock.patch("app.api.v1.routes.files.s3_client", return_value=dummy_s3), mock.patch(
            "app.workers.tasks.enqueue_convert_file",
            return_value="job-auto-flow",
        ):
            with self._db() as db:
                payload = asyncio.run(
                    file_routes.direct_upload(
                        upload=upload,
                        project_id=None,
                        projectId=None,
                        db=db,
                        principal=self.current_principal,
                    )
                ).model_dump()

        self.assertEqual(payload["status"], "queued")
        self.assertTrue(payload["file_id"].startswith("scx_"))
        self.assertEqual(len(dummy_s3.uploads), 1)

        with self._db() as db:
            decision = orchestrator_routes.get_orchestrator_decision(
                file_id=payload["file_id"],
                db=db,
                principal=self.current_principal,
            ).model_dump()
        self.assertEqual(decision["state"], "S0")
        self.assertEqual(decision["file_id"], payload["file_id"])

    def test_auto_mode_promotes_ready_flow_without_manual_advance(self) -> None:
        geometry_meta = {
            "bbox": {"x": 120.0, "y": 64.0, "z": 28.0},
            "diagonal": 139.83,
            "part_count": 1,
        }
        dfm_findings = {"status_gate": "PASS", "findings": [], "risk_flags": []}
        decision_json = build_decision_json(
            mode="brep",
            rule_version="v1.0",
            geometry_meta=geometry_meta,
            dfm_findings=dfm_findings,
        )
        file_id = self._seed_file(
            meta={
                "decision_json": decision_json,
                "geometry_meta_json": geometry_meta,
                "dfm_findings": dfm_findings,
            },
            decision_json=decision_json,
        )

        with self._db() as db:
            decision_payload = orchestrator_routes.get_orchestrator_decision(
                file_id=file_id,
                db=db,
                principal=self.current_principal,
            ).model_dump()
        self.assertEqual(decision_payload["state"], "S6")
        self.assertEqual(decision_payload["decision_json"]["rule_version"], "v1.0")
        self.assertNotIn("decision_fallback_used", decision_payload["decision_json"]["conflict_flags"])

        with self._db() as db:
            session = db.query(OrchestratorSession).filter(OrchestratorSession.file_id == file_id).first()
            self.assertIsNotNone(session)
            self.assertEqual(session.state, "S6")
            self.assertEqual(session.status_gate, "PASS")

    def test_required_inputs_auto_resume_after_submission(self) -> None:
        file_id = self._seed_file(
            original_filename="fallback.png",
            content_type="image/png",
            kind="image",
            mode="visual_only",
            ready_contract=False,
            meta={"decision_json": {}},
            decision_json={},
        )

        with self._db() as db:
            decision_payload = orchestrator_routes.get_orchestrator_decision(
                file_id=file_id,
                db=db,
                principal=self.current_principal,
            ).model_dump()
        session_id = decision_payload["session_id"]
        self.assertEqual(decision_payload["decision_json"]["manufacturing_method"], "unknown")

        with self._db() as db:
            required_payload = orchestrator_routes.get_required_inputs(
                session_id=session_id,
                db=db,
                principal=self.current_principal,
            ).model_dump()
        self.assertEqual(required_payload["required_inputs"][0]["key"], "manufacturing_intent")
        self.assertEqual(required_payload["blocked_reasons"][0]["code"], "missing_required_inputs")

        with self._db() as db:
            accepted = orchestrator_routes.submit_orchestrator_input(
                data=orchestrator_routes.OrchestratorInputIn(
                    session_id=session_id,
                    key="manufacturing_intent",
                    value="cnc",
                ),
                db=db,
                principal=self.current_principal,
            ).model_dump()
        self.assertEqual(accepted["required_inputs"], [])
        self.assertEqual(accepted["state"], "S6")

        with self._db() as db:
            resumed = orchestrator_routes.get_orchestrator_decision(
                session_id=session_id,
                db=db,
                principal=self.current_principal,
            ).model_dump()
        self.assertEqual(resumed["state"], "S6")
        self.assertEqual(resumed["decision_json"]["manufacturing_method"], "cnc")
        self.assertNotIn("decision_fallback_used", resumed["decision_json"]["conflict_flags"])

    def test_invalid_state_transition_is_rejected(self) -> None:
        decision_json = build_decision_json(mode="brep", rule_version="v1.0")
        file_id = self._seed_file(meta={"decision_json": decision_json}, decision_json=decision_json)
        session_id = self._seed_session(file_id=file_id, state="S0", decision_json=decision_json)

        with self._db() as db:
            with self.assertRaises(HTTPException) as blocked:
                approval_routes.approve_session(
                    session_id=session_id,
                    data=approval_routes.ApprovalIn(reason="invalid"),
                    db=db,
                    principal=self.current_principal,
                )
        self.assertEqual(blocked.exception.status_code, 409)

    def test_share_create_resolve_revoke_and_expire_behave_explicitly(self) -> None:
        file_id = self._seed_file()
        with mock.patch("app.api.v1.routes.share._enforce_share_rate_limit", return_value=None):
            with self._db() as db:
                share_payload = share_routes.create_share(
                    data=share_routes.ShareCreateIn(
                        file_id=file_id,
                        permission="view",
                        expires_in_seconds=3600,
                    ),
                    db=db,
                    principal=self.current_principal,
                ).model_dump()

            with self._db() as db:
                resolved = share_routes.resolve_share(
                    token=share_payload["token"],
                    request=self._request(f"/api/v1/share/{share_payload['token']}"),
                    db=db,
                ).model_dump()
            self.assertEqual(resolved["original_filename"], "part.step")

            with self._db() as db:
                revoked = share_routes.revoke_share(
                    share_id=share_payload["id"],
                    db=db,
                    principal=self.current_principal,
                )
            self.assertEqual(revoked["status"], "ok")

            with self._db() as db:
                with self.assertRaises(HTTPException) as denied:
                    share_routes.resolve_share(
                        token=share_payload["token"],
                        request=self._request(f"/api/v1/share/{share_payload['token']}"),
                        db=db,
                    )
            self.assertEqual(denied.exception.status_code, 403)

            expired_share_id, expired_token = self._seed_share(
                file_id=file_id,
                expires_at=datetime.now(timezone.utc) - timedelta(minutes=5),
            )
            self.assertTrue(expired_share_id)
            with self._db() as db:
                with self.assertRaises(HTTPException) as expired:
                    share_routes.resolve_share(
                        token=expired_token,
                        request=self._request(f"/api/v1/share/{expired_token}"),
                        db=db,
                    )
            self.assertEqual(expired.exception.status_code, 410)

    def test_admin_health_failed_jobs_and_audit_payloads_are_safe(self) -> None:
        type(self).current_principal = Principal(typ="user", user_id=str(self.admin_uuid), role="admin")
        legacy_file_id = str(uuid.uuid4())
        self._seed_file(stored_file_id=legacy_file_id)
        self._seed_failure(file_id=legacy_file_id)
        with self._db() as db:
            db.add(
                AuditEvent(
                    event_type="share.created",
                    actor_user_id=self.admin_uuid,
                    actor_anon_sub=None,
                    file_id=legacy_file_id,
                    data={
                        "bucket": "private-bucket",
                        "object_key": "secret/object",
                        "storage_key": "secret/storage",
                        "safe": "value",
                    },
                )
            )

        def _queue_for_name(name: str) -> _DummyQueue:
            return _DummyQueue({"cad": 2, "drawing": 3, "render": 4}[name])

        dummy_s3 = _DummyS3()
        with mock.patch("app.api.v1.routes.admin.get_queue", side_effect=_queue_for_name), mock.patch(
            "app.api.v1.routes.admin.Worker.all",
            return_value=[object()],
        ), mock.patch(
            "app.api.v1.routes.admin.redis_conn.ping",
            return_value=True,
        ), mock.patch(
            "app.api.v1.routes.admin.get_s3_client",
            return_value=dummy_s3,
        ):
            with self._db() as db:
                health_payload = admin_routes.admin_health(db=db)
            self.assertEqual(health_payload["api"], "ok")
            self.assertEqual(health_payload["db"], "ok")
            self.assertEqual(health_payload["worker"], "ok")
            self.assertEqual(health_payload["queue_depth"], 9)
            self.assertEqual(health_payload["failed_jobs"], 1)

        with self._db() as db:
            failed_payload = admin_routes.admin_failed_jobs(db=db)["items"][0]
        self.assertEqual(failed_payload["file_id"], self._public_file_id(legacy_file_id))
        self.assertEqual(failed_payload["failure_code"], "CONVERT_RUNTIMEERROR")

        with self._db() as db:
            audit_payload = admin_routes.admin_audit(db=db)["items"][0]
        self.assertEqual(audit_payload["file_id"], self._public_file_id(legacy_file_id))
        self.assertEqual(audit_payload["meta_preview"]["safe"], "value")
        self.assertNotIn("bucket", audit_payload["meta_preview"])
        self.assertNotIn("object_key", audit_payload["meta_preview"])
        self.assertNotIn("storage_key", audit_payload["meta_preview"])

    def test_file_status_fail_closed_when_assembly_truth_missing(self) -> None:
        file_id = self._seed_file(
            ready_contract=False,
            meta={"preview_jpg_keys": ["preview/0.jpg"]},
        )
        with self._db() as db:
            row = db.query(UploadFileModel).filter(UploadFileModel.file_id == file_id).first()
            row.gltf_key = f"glb/{file_id}.glb"
            row.thumbnail_key = f"thumb/{file_id}.webp"
            db.add(row)

        with self._db() as db:
            payload = file_routes.file_status(file_id=file_id, db=db, principal=self.current_principal).model_dump()
        self.assertEqual(payload["state"], "failed")
        self.assertNotIn("assembly_meta", payload["derivatives_available"])

    def test_projects_surface_normalizes_public_file_identity(self) -> None:
        legacy_file_id = str(uuid.uuid4())
        self._seed_file(stored_file_id=legacy_file_id)

        with self._db() as db:
            payload = [item.model_dump() for item in platform_contract_routes.list_projects(db=db, principal=self.current_principal)]
        self.assertEqual(payload[0]["files"][0]["file_id"], self._public_file_id(legacy_file_id))

    def test_product_status_fail_closes_legacy_revision_urls(self) -> None:
        file_id = self._seed_file()

        with self._db() as db:
            payload = product_routes.status(revision_id=file_id, db=db).model_dump()
        self.assertEqual(payload["file_id"], file_id)
        self.assertEqual(payload["jobs"], [])
        self.assertTrue(payload["artifacts"])
        self.assertTrue(all(str(item["url"]).startswith("/api/v1/files/") for item in payload["artifacts"] if item["url"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
