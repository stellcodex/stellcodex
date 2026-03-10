from __future__ import annotations

import json
import unittest
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.v1.routes.knowledge import (
    KnowledgeIndexIn,
    KnowledgeSearchIn,
    index_knowledge,
    search_knowledge,
)
from app.core.events import EventEnvelope
from app.db.base import Base
from app.knowledge.normalizers import (
    canonical_record,
    normalize_assembly_meta,
    normalize_decision_json,
    normalize_dfm_report,
    normalize_engineering_report,
)
from app.knowledge.providers import BM25SparseProvider, HashEmbeddingProvider, InMemoryVectorIndexProvider
from app.knowledge.service import KnowledgeService, get_knowledge_service
from app.models.audit import AuditEvent
from app.models.core import Job, JobStatus, JobType, Privacy, Project, Revision
from app.models.file import UploadFile
from app.models.knowledge import KnowledgeIndexJob, KnowledgeRecord
from app.models.master_contract import FileRegistry, FileVersion, JobLog, Tenant
from app.models.orchestrator import OrchestratorSession, RuleConfig
from app.models.phase2 import ProcessedEventId
from app.security.deps import Principal
from app.services.tenant_identity import tenant_code_for_owner
from app.stellai.knowledge import get_context_bundle
from app.stellai.types import RuntimeContext


def _create_test_service() -> KnowledgeService:
    return KnowledgeService(
        index_version="test-v1",
        embedding_provider=HashEmbeddingProvider(_dim=96),
        vector_index_provider=InMemoryVectorIndexProvider(),
        sparse_search_provider=BM25SparseProvider(),
    )


class KnowledgeEnginePhaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite:///:memory:")
        self.Session = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        Base.metadata.create_all(
            bind=self.engine,
            tables=[
                Tenant.__table__,
                UploadFile.__table__,
                OrchestratorSession.__table__,
                RuleConfig.__table__,
                AuditEvent.__table__,
                FileRegistry.__table__,
                FileVersion.__table__,
                JobLog.__table__,
                Project.__table__,
                Revision.__table__,
                Job.__table__,
                ProcessedEventId.__table__,
                KnowledgeRecord.__table__,
                KnowledgeIndexJob.__table__,
            ],
        )
        self.db = self.Session()
        self.service = _create_test_service()
        get_knowledge_service.cache_clear()
        self._seed()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def _seed(self) -> None:
        self.tenant_1 = 101
        self.tenant_2 = 202
        self.db.add(
            Tenant(
                id=self.tenant_1,
                code=tenant_code_for_owner("guest-1"),
                name="Guest 1",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )
        self.db.add(
            Tenant(
                id=self.tenant_2,
                code=tenant_code_for_owner("guest-2"),
                name="Guest 2",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
        )

        now = datetime.now(timezone.utc)

        decision_1 = {
            "manufacturing_method": "cnc_milling",
            "mode": "brep",
            "confidence": 0.91,
            "rule_version": "v7.0.0",
            "rule_explanations": ["deterministic rule hit for cnc milling"],
            "conflict_flags": [],
            "risk_flags": ["thin_wall"],
        }
        decision_2 = {
            "manufacturing_method": "injection_molding",
            "mode": "visual_only",
            "confidence": 0.44,
            "rule_version": "v7.0.0",
            "rule_explanations": ["deterministic rule hit for injection"],
            "conflict_flags": ["visual_only_mode"],
            "risk_flags": ["visual_only_mode"],
        }
        dfm_report = {
            "recommendations": ["Increase fillet radius", "Review undercut geometry"],
            "risks": [
                {"category": "wall_thickness", "severity": "high"},
                {"category": "undercut", "severity": "medium"},
            ],
            "decision_json": decision_1,
        }
        engineering_report = {
            "schema": "stellcodex.v1.engineering_report",
            "manufacturing_recommendation": {
                "recommended_process": "cnc_machining",
                "capability_status": "supported",
            },
            "manufacturing_plan": {
                "process_sequence": ["raw_material_preparation", "rough_machining", "inspection"],
                "machine_requirements": ["3-axis CNC mill"],
            },
            "cost_estimate": {
                "estimated_unit_cost": 42.5,
                "currency": "EUR",
                "capability_status": "supported",
            },
            "dfm_report": {
                "risk_count": 2,
            },
            "design_improvements": ["Review thin sections", "Add draft where needed"],
            "capability_status": "supported",
        }
        assembly_meta = {
            "occurrences": [
                {"occurrence_id": "root", "name": "MainBody", "part_id": "P-100"},
                {"occurrence_id": "mesh-node", "name": "MeshNode_01", "part_id": "mesh-01"},
            ]
        }
        self.file_1 = UploadFile(
            file_id="scx_11111111-1111-1111-1111-111111111111",
            owner_sub="guest-1",
            tenant_id=self.tenant_1,
            owner_user_id=None,
            owner_anon_sub="guest-1",
            is_anonymous=True,
            privacy="private",
            bucket="tenant-1",
            object_key="uploads/tenant_1/demo.step",
            original_filename="demo.step",
            content_type="application/step",
            size_bytes=1024,
            status="ready",
            visibility="private",
            folder_key="project/p1/3d/brep",
            meta={
                "project_id": "p1",
                "kind": "3d",
                "mode": "brep",
                "dfm_report_json": dfm_report,
                "engineering_report": engineering_report,
                "assembly_meta": assembly_meta,
                "assembly_meta_key": "metadata/private/assembly_meta.json",
                "production_package_key": "packages/private/package.zip",
                "error_code": "DFM_WARN",
                "error": "thin wall risk",
            },
            decision_json=decision_1,
            created_at=now,
            updated_at=now,
        )
        self.file_2 = UploadFile(
            file_id="scx_22222222-2222-2222-2222-222222222222",
            owner_sub="guest-2",
            tenant_id=self.tenant_2,
            owner_user_id=None,
            owner_anon_sub="guest-2",
            is_anonymous=True,
            privacy="private",
            bucket="tenant-2",
            object_key="uploads/tenant_2/demo.step",
            original_filename="demo.step",
            content_type="application/step",
            size_bytes=1024,
            status="ready",
            visibility="private",
            folder_key="project/p2/3d/brep",
            meta={"project_id": "p2", "kind": "3d", "mode": "visual_only"},
            decision_json=decision_2,
            created_at=now,
            updated_at=now,
        )
        self.db.add(self.file_1)
        self.db.add(self.file_2)

        session = OrchestratorSession(
            file_id=self.file_1.file_id,
            state="S7",
            state_code="S7",
            state_label="share_ready",
            status_gate="PASS",
            approval_required=False,
            rule_version="v7.0.0",
            mode="brep",
            confidence=0.91,
            risk_flags=["thin_wall"],
            decision_json=decision_1,
            notes="ready",
            created_at=now,
            updated_at=now,
        )
        self.db.add(session)
        self.db.add(
            RuleConfig(
                key="wall_mm_min",
                value_json={"scope": "global", "value": 1.0, "version": "v7.0.0"},
                enabled=True,
                description="min wall",
                created_at=now,
                updated_at=now,
            )
        )
        self.db.add(
            AuditEvent(
                event_type="approval.approved",
                actor_user_id=None,
                actor_anon_sub="guest-1",
                file_id=self.file_1.file_id,
                data={"tenant_id": str(self.tenant_1), "project_id": "p1"},
                created_at=now,
            )
        )
        project = Project(id=uuid4(), name="P1", owner_id="guest-1", privacy=Privacy.PRIVATE, created_at=now)
        revision = Revision(id=uuid4(), project_id=project.id, label="r1", created_at=now)
        self.db.add(project)
        self.db.add(revision)
        self.db.add(
            Job(
                id=uuid4(),
                rev_uid=revision.id,
                type=JobType.CAD_LOD0,
                status=JobStatus.SUCCEEDED,
                queue="cad",
                error=None,
                created_at=now,
                started_at=now,
                finished_at=now,
            )
        )
        self.db.add(FileRegistry(id=self.file_1.file_id, file_id=self.file_1.file_id, uploaded_file_id=self.file_1.file_id, created_at=now, updated_at=now))
        self.db.add(
            FileVersion(
                id=1,
                file_id=self.file_1.file_id,
                version_no=1,
                uploaded_file_id=self.file_1.file_id,
                created_at=now,
            )
        )
        self.db.add(
            JobLog(
                id=1,
                job_id="job-1",
                file_id=self.file_1.file_id,
                stage="dfm",
                message="dfm completed",
                payload={"tenant_id": str(self.tenant_1), "project_id": "p1"},
                immutable=True,
                created_at=now,
            )
        )
        self.db.commit()

    def test_normalizers_extract_required_fields(self) -> None:
        decision = normalize_decision_json(self.file_1.decision_json)
        self.assertEqual(decision["metadata"]["manufacturing_method"], "cnc_milling")
        self.assertEqual(decision["metadata"]["rule_version"], "v7.0.0")

        dfm = normalize_dfm_report(self.file_1.meta["dfm_report_json"])
        self.assertIn("wall_thickness", dfm["metadata"]["risk_categories"])
        self.assertIn("high", dfm["metadata"]["severity"])

        assembly = normalize_assembly_meta(self.file_1.meta["assembly_meta"])
        self.assertIn("MainBody", assembly["metadata"]["component_names"])
        self.assertNotIn("MeshNode_01", assembly["metadata"]["component_names"])

        engineering = normalize_engineering_report(self.file_1.meta["engineering_report"])
        self.assertEqual(engineering["metadata"]["recommended_process"], "cnc_machining")
        self.assertEqual(engineering["metadata"]["risk_count"], 2)

    def test_hash_idempotency_and_hybrid_ranking(self) -> None:
        rec1 = canonical_record(
            tenant_id=str(self.tenant_1),
            project_id="p1",
            file_id=self.file_1.file_id,
            source_type="database",
            source_subtype="decision_json",
            source_ref=f"scx://files/{self.file_1.file_id}/decision_json",
            title="decision",
            text="deterministic cnc milling decision",
            metadata={"mode": "brep"},
            tags=["decision"],
            index_version="test-v1",
        )
        rec2 = canonical_record(
            tenant_id=str(self.tenant_1),
            project_id="p1",
            file_id=self.file_1.file_id,
            source_type="database",
            source_subtype="decision_json",
            source_ref=f"scx://files/{self.file_1.file_id}/decision_json",
            title="decision",
            text="deterministic cnc milling decision",
            metadata={"mode": "brep"},
            tags=["decision"],
            index_version="test-v1",
        )
        self.assertEqual(rec1.hash_sha256, rec2.hash_sha256)
        self.assertEqual(rec1.record_id, rec2.record_id)

        summary = self.service.index_scope(
            db=self.db,
            tenant_id=str(self.tenant_1),
            project_id="p1",
            file_id=self.file_1.file_id,
            source_types=["database", "artifacts", "events"],
            include_events=True,
        )
        self.db.commit()
        self.assertGreater(summary["indexed"], 0)
        self.assertTrue(
            any(row.source_subtype == "engineering_report" for row in self.db.query(KnowledgeRecord).all())
        )

        hits = self.service.search_knowledge(
            db=self.db,
            query="cnc milling deterministic",
            tenant_id=str(self.tenant_1),
            project_id="p1",
            top_k=5,
        )
        self.assertTrue(hits)
        self.assertTrue(any(self.file_1.file_id in item["source_ref"] for item in hits))

    def test_ingestion_worker_idempotent_replay_and_retry(self) -> None:
        first = self.service.ingest_event(
            db=self.db,
            envelope=EventEnvelope.build(
                event_type="file.ready",
                source="test",
                subject=self.file_1.file_id,
                tenant_id=str(self.tenant_1),
                project_id="p1",
                event_id="evt-file-ready-1",
                data={"file_id": self.file_1.file_id, "version_no": 1},
            ),
        )
        self.db.commit()
        self.assertIn(first["status"], {"indexed", "skipped"})
        second = self.service.ingest_event(
            db=self.db,
            envelope=EventEnvelope.build(
                event_type="file.ready",
                source="test",
                subject=self.file_1.file_id,
                tenant_id=str(self.tenant_1),
                project_id="p1",
                event_id="evt-file-ready-1",
                data={"file_id": self.file_1.file_id, "version_no": 1},
            ),
        )
        self.assertEqual(second["status"], "skipped")

        failed = self.service.ingest_event(
            db=self.db,
            envelope=EventEnvelope.build(
                event_type="decision.produced",
                source="test",
                subject="missing",
                tenant_id=str(self.tenant_1),
                project_id="p1",
                event_id="evt-retry-1",
                data={},
            ),
        )
        self.assertEqual(failed["status"], "failed")
        self.assertIn(failed["failure_code"], {"INVALID_PAYLOAD", "SOURCE_NOT_FOUND"})
        self.db.commit()

        retried = self.service.ingest_event(
            db=self.db,
            envelope=EventEnvelope.build(
                event_type="decision.produced",
                source="test",
                subject=self.file_1.file_id,
                tenant_id=str(self.tenant_1),
                project_id="p1",
                event_id="evt-retry-1",
                data={"file_id": self.file_1.file_id},
            ),
        )
        self.assertIn(retried["status"], {"indexed", "skipped"})

    def test_api_tenant_isolation_and_no_storage_key_leak(self) -> None:
        principal = Principal(typ="guest", owner_sub="guest-1", anon=True)

        index_payload = index_knowledge(
            KnowledgeIndexIn(
                file_id=self.file_1.file_id,
                project_id="p1",
                source_types=["database", "artifacts", "events"],
            ),
            db=self.db,
            principal=principal,
        )
        self.assertEqual(index_payload.status, "ok")

        search_payload = search_knowledge(
            KnowledgeSearchIn(query="cnc milling", project_id="p1", top_k=10),
            db=self.db,
            principal=principal,
        )
        payload = search_payload.model_dump() if hasattr(search_payload, "model_dump") else search_payload.dict()
        text_dump = json.dumps(payload, ensure_ascii=True).lower()
        self.assertNotIn("storage_key", text_dump)
        self.assertNotIn("object_key", text_dump)
        self.assertNotIn("\"bucket\"", text_dump)
        self.assertNotIn(self.file_2.file_id.lower(), text_dump)

    def test_stellai_context_bundle_retrieval(self) -> None:
        shared_service = get_knowledge_service()
        shared_service.reindex_scope(
            db=self.db,
            tenant_id=str(self.tenant_1),
            project_id="p1",
            file_id=self.file_1.file_id,
            source_types=["database", "artifacts", "events"],
            document_paths=[],
        )
        shared_service.index_scope(
            db=self.db,
            tenant_id=str(self.tenant_1),
            project_id="p1",
            file_id=self.file_1.file_id,
            source_types=["database", "artifacts", "events"],
            include_events=True,
        )
        self.db.commit()
        context = RuntimeContext(
            tenant_id=str(self.tenant_1),
            project_id="p1",
            principal_type="guest",
            principal_id="guest-1",
            session_id="sess-1",
            trace_id="trace-1",
            file_ids=(self.file_1.file_id,),
            allowed_tools=frozenset(),
        )
        bundle = get_context_bundle(db=self.db, context=context, query="deterministic cnc decision", top_k=5)
        refs = bundle.get("source_references", [])
        self.assertTrue(refs)
        self.assertTrue(any(self.file_1.file_id in ref for ref in refs))
        self.assertFalse(any(self.file_2.file_id in ref for ref in refs))


if __name__ == "__main__":
    unittest.main()
