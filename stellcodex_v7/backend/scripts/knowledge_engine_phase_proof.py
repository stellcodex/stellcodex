from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test_stellcodex")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-unit-tests-only-32chars!!")

from app.core.events import EventEnvelope
from app.db.base import Base
from app.knowledge.providers import BM25SparseProvider, HashEmbeddingProvider, InMemoryVectorIndexProvider
from app.knowledge.service import KnowledgeService
from app.models.audit import AuditEvent
from app.models.core import Job, JobStatus, JobType, Privacy, Project, Revision
from app.models.file import UploadFile
from app.models.knowledge import KnowledgeIndexJob, KnowledgeRecord
from app.models.master_contract import FileRegistry, FileVersion, JobLog, Tenant
from app.models.orchestrator import OrchestratorSession, RuleConfig
from app.models.phase2 import ProcessedEventId
from app.services.tenant_identity import tenant_code_for_owner
from app.stellai.knowledge import get_context_bundle
from app.stellai.types import RuntimeContext


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _service() -> KnowledgeService:
    return KnowledgeService(
        index_version="proof-v1",
        embedding_provider=HashEmbeddingProvider(_dim=96),
        vector_index_provider=InMemoryVectorIndexProvider(),
        sparse_search_provider=BM25SparseProvider(),
    )


def _seed(db) -> tuple[int, int, str, str]:
    tenant_1 = 701
    tenant_2 = 702
    db.add(
        Tenant(
            id=tenant_1,
            code=tenant_code_for_owner("proof-guest-1"),
            name="Proof Guest 1",
            created_at=_now(),
            updated_at=_now(),
        )
    )
    db.add(
        Tenant(
            id=tenant_2,
            code=tenant_code_for_owner("proof-guest-2"),
            name="Proof Guest 2",
            created_at=_now(),
            updated_at=_now(),
        )
    )
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
    assembly_meta = {
        "occurrences": [
            {"occurrence_id": "root", "name": "MainBody", "part_id": "P-100"},
            {"occurrence_id": "mesh-node", "name": "MeshNode_01", "part_id": "mesh-01"},
        ]
    }
    file_1 = "scx_aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    file_2 = "scx_bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    shared_now = _now()
    db.add(
        UploadFile(
            file_id=file_1,
            owner_sub="proof-guest-1",
            tenant_id=tenant_1,
            owner_user_id=None,
            owner_anon_sub="proof-guest-1",
            is_anonymous=True,
            privacy="private",
            bucket="tenant-1",
            object_key="uploads/tenant_1/proof.step",
            original_filename="proof.step",
            content_type="application/step",
            size_bytes=1000,
            status="ready",
            visibility="private",
            folder_key="project/p-proof/3d/brep",
            meta={
                "project_id": "p-proof",
                "kind": "3d",
                "mode": "brep",
                "dfm_report_json": dfm_report,
                "assembly_meta": assembly_meta,
                "assembly_meta_key": "metadata/private/assembly_meta.json",
                "production_package_key": "packages/private/package.zip",
            },
            decision_json=decision_1,
            created_at=shared_now,
            updated_at=shared_now,
        )
    )
    db.add(
        UploadFile(
            file_id=file_2,
            owner_sub="proof-guest-2",
            tenant_id=tenant_2,
            owner_user_id=None,
            owner_anon_sub="proof-guest-2",
            is_anonymous=True,
            privacy="private",
            bucket="tenant-2",
            object_key="uploads/tenant_2/proof.step",
            original_filename="proof.step",
            content_type="application/step",
            size_bytes=1000,
            status="ready",
            visibility="private",
            folder_key="project/p-proof-2/3d/brep",
            meta={"project_id": "p-proof-2", "kind": "3d", "mode": "visual_only"},
            decision_json=decision_2,
            created_at=shared_now,
            updated_at=shared_now,
        )
    )
    db.add(
        OrchestratorSession(
            file_id=file_1,
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
            created_at=shared_now,
            updated_at=shared_now,
        )
    )
    db.add(
        RuleConfig(
            key="wall_mm_min",
            value_json={"scope": "global", "value": 1.0, "version": "v7.0.0"},
            enabled=True,
            description="min wall",
            created_at=shared_now,
            updated_at=shared_now,
        )
    )
    db.add(
        AuditEvent(
            event_type="approval.approved",
            actor_user_id=None,
            actor_anon_sub="proof-guest-1",
            file_id=file_1,
            data={"tenant_id": str(tenant_1), "project_id": "p-proof"},
            created_at=shared_now,
        )
    )
    project = Project(id=uuid4(), name="proof", owner_id="proof-guest-1", privacy=Privacy.PRIVATE, created_at=shared_now)
    revision = Revision(id=uuid4(), project_id=project.id, label="r1", created_at=shared_now)
    db.add(project)
    db.add(revision)
    db.add(
        Job(
            id=uuid4(),
            rev_uid=revision.id,
            type=JobType.CAD_LOD0,
            status=JobStatus.SUCCEEDED,
            queue="cad",
            error=None,
            created_at=shared_now,
            started_at=shared_now,
            finished_at=shared_now,
        )
    )
    db.add(FileRegistry(id=file_1, file_id=file_1, uploaded_file_id=file_1, created_at=shared_now, updated_at=shared_now))
    db.add(FileVersion(id=1, file_id=file_1, version_no=1, uploaded_file_id=file_1, created_at=shared_now))
    db.add(
        JobLog(
            id=1,
            job_id="proof-job",
            file_id=file_1,
            stage="dfm",
            message="dfm completed",
            payload={"tenant_id": str(tenant_1), "project_id": "p-proof"},
            immutable=True,
            created_at=shared_now,
        )
    )
    db.commit()
    return tenant_1, tenant_2, file_1, file_2


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Knowledge Engine runtime proof bundle")
    parser.add_argument("--evidence-dir", default="/root/workspace/evidence/knowledge_engine_phase")
    args = parser.parse_args()

    evidence_dir = Path(args.evidence_dir).resolve()
    evidence_dir.mkdir(parents=True, exist_ok=True)

    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(
        bind=engine,
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
    db = Session()
    service = _service()
    tenant_1, tenant_2, file_1, file_2 = _seed(db)

    index_summary = service.index_scope(
        db=db,
        tenant_id=str(tenant_1),
        project_id="p-proof",
        file_id=file_1,
        source_types=["database", "artifacts", "events"],
        include_events=True,
    )
    db.commit()

    search_tenant_1 = service.search_knowledge(
        db=db,
        query="deterministic cnc milling decision",
        tenant_id=str(tenant_1),
        project_id="p-proof",
        top_k=8,
    )
    search_tenant_2 = service.search_knowledge(
        db=db,
        query="deterministic cnc milling decision",
        tenant_id=str(tenant_2),
        project_id="p-proof-2",
        top_k=8,
    )

    first_event = service.ingest_event(
        db=db,
        envelope=EventEnvelope.build(
            event_type="file.ready",
            source="proof.script",
            subject=file_1,
            tenant_id=str(tenant_1),
            project_id="p-proof",
            event_id="evt-proof-file-ready",
            data={"file_id": file_1, "version_no": 1},
        ),
    )
    db.commit()
    duplicate_event = service.ingest_event(
        db=db,
        envelope=EventEnvelope.build(
            event_type="file.ready",
            source="proof.script",
            subject=file_1,
            tenant_id=str(tenant_1),
            project_id="p-proof",
            event_id="evt-proof-file-ready",
            data={"file_id": file_1, "version_no": 1},
        ),
    )

    reindex_summary = service.reindex_scope(
        db=db,
        tenant_id=str(tenant_1),
        project_id="p-proof",
        file_id=file_1,
        source_types=["database", "artifacts", "events"],
        document_paths=[],
    )
    db.commit()

    context_bundle = get_context_bundle(
        db=db,
        context=RuntimeContext(
            tenant_id=str(tenant_1),
            project_id="p-proof",
            principal_type="proof",
            principal_id="proof-guest-1",
            session_id="proof-session",
            trace_id=str(uuid4()),
            file_ids=(file_1,),
            allowed_tools=frozenset(),
        ),
        query="deterministic cnc milling decision",
        top_k=6,
    )
    sample_record = {}
    if search_tenant_1:
        sample_record = service.get_record(db=db, record_id=search_tenant_1[0]["record_id"], tenant_id=str(tenant_1)) or {}

    worker_log_path = Path("/root/workspace/_truth/logs/knowledge_worker.jsonl")
    worker_log_lines = []
    if worker_log_path.exists():
        worker_log_lines = [line for line in worker_log_path.read_text(encoding="utf-8", errors="ignore").splitlines() if line.strip()][-20:]

    no_leak_blob = json.dumps(
        {
            "search_tenant_1": search_tenant_1,
            "sample_record": sample_record,
            "context_bundle": context_bundle,
        },
        ensure_ascii=True,
    ).lower()
    no_leak_verification = {
        "contains_storage_key": "storage_key" in no_leak_blob,
        "contains_object_key": "object_key" in no_leak_blob,
        "contains_bucket_literal": "\"bucket\"" in no_leak_blob,
    }

    tenant_isolation_verification = {
        "tenant_1_result_count": len(search_tenant_1),
        "tenant_2_result_count": len(search_tenant_2),
        "tenant_1_has_file_2": any(file_2 in item.get("source_ref", "") for item in search_tenant_1),
        "tenant_2_has_file_1": any(file_1 in item.get("source_ref", "") for item in search_tenant_2),
    }

    artifacts = {
        "index_summary.json": index_summary,
        "search_results_tenant1.json": search_tenant_1,
        "search_results_tenant2.json": search_tenant_2,
        "ingest_event_first.json": first_event,
        "ingest_event_duplicate.json": duplicate_event,
        "reindex_summary.json": reindex_summary,
        "context_bundle.json": context_bundle,
        "sample_record.json": sample_record,
        "tenant_isolation_verification.json": tenant_isolation_verification,
        "no_leak_verification.json": no_leak_verification,
        "worker_logs.json": worker_log_lines,
        "health.json": service.health(db=db),
    }
    for filename, payload in artifacts.items():
        (evidence_dir / filename).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "evidence_dir": str(evidence_dir),
        "files_written": sorted(artifacts.keys()),
        "index_status": index_summary.get("status"),
        "indexed": index_summary.get("indexed"),
        "search_results": len(search_tenant_1),
        "tenant_isolation": tenant_isolation_verification,
        "no_leak": no_leak_verification,
    }
    (evidence_dir / "runtime_proof_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    db.close()
    engine.dispose()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
