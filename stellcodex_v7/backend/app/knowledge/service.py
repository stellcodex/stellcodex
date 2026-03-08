from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.core.events import EventEnvelope
from app.knowledge.normalizers import (
    canonical_record,
    normalize_assembly_meta,
    normalize_audit_event,
    normalize_decision_json,
    normalize_dfm_report,
    normalize_document,
    normalize_rule_config,
    sanitize_public_payload,
)
from app.knowledge.providers import (
    EmbeddingProvider,
    SparseSearchProvider,
    VectorIndexProvider,
    build_embedding_provider,
    build_sparse_provider,
    build_vector_provider,
)
from app.knowledge.types import (
    FAILURE_EMBEDDING_FAIL,
    FAILURE_INDEX_WRITE_FAIL,
    FAILURE_INVALID_PAYLOAD,
    FAILURE_NORMALIZATION_FAIL,
    FAILURE_SOURCE_NOT_FOUND,
    INDEX_STATUS_FAILED,
    INDEX_STATUS_INDEXED,
    INDEX_STATUS_PENDING,
    INDEX_STATUS_SKIPPED,
    INDEX_VERSION_DEFAULT,
    CanonicalKnowledgeRecord,
)
from app.models.audit import AuditEvent
from app.models.core import Job, Project
from app.models.file import UploadFile
from app.models.knowledge import KnowledgeIndexJob, KnowledgeRecord
from app.models.master_contract import FileRegistry, FileVersion, JobLog
from app.models.orchestrator import OrchestratorSession, RuleConfig
from app.models.phase2 import ProcessedEventId


_WORKER_LOG_PATH = Path("/root/workspace/_truth/logs/knowledge_worker.jsonl")
_WORKSPACE_ROOT = Path("/root/workspace")
_DEFAULT_DOC_PATTERNS = (
    "docs/**/*.md",
    "_truth/**/*.md",
    "README.md",
    "PHASE2_*.md",
)
_APPROVAL_EVENTS = ("approval.approved", "approval.rejected", "approval.changed")
_TRIGGER_EVENTS = {
    "file.ready",
    "package.ready",
    "assembly.ready",
    "dfm.completed",
    "dfm.ready",
    "decision.produced",
    "decision.ready",
    "approval.changed",
    "approval.approved",
    "approval.rejected",
    "audit.logged",
    "document.imported",
}


def _now() -> datetime:
    return datetime.utcnow()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _append_worker_log(payload: dict[str, Any]) -> None:
    try:
        _WORKER_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with _WORKER_LOG_PATH.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    except Exception:
        return


class KnowledgeService:
    def __init__(
        self,
        *,
        index_version: str = INDEX_VERSION_DEFAULT,
        embedding_provider: EmbeddingProvider | None = None,
        vector_index_provider: VectorIndexProvider | None = None,
        sparse_search_provider: SparseSearchProvider | None = None,
    ) -> None:
        self.index_version = str(index_version or INDEX_VERSION_DEFAULT)
        self.embedding_provider = embedding_provider or build_embedding_provider()
        self.vector_index_provider = vector_index_provider or build_vector_provider()
        self.sparse_search_provider = sparse_search_provider or build_sparse_provider()
        self._indexed_ids: set[str] = set()
        self._cache_loaded = False

    def health(self, *, db: Session) -> dict[str, Any]:
        return {
            "status": "ok",
            "index_version": self.index_version,
            "embedding_model": str(self.embedding_provider.model_name),
            "embedding_dim": int(self.embedding_provider.dim),
            "vector_provider": str(self.vector_index_provider.name),
            "sparse_provider": str(self.sparse_search_provider.name),
            "record_count": db.query(KnowledgeRecord).filter(KnowledgeRecord.index_version == self.index_version).count(),
            "job_count": db.query(KnowledgeIndexJob).count(),
            "worker_log_path": str(_WORKER_LOG_PATH),
        }

    def rebuild_from_canonical(self, *, db: Session) -> dict[str, Any]:
        self.vector_index_provider.clear()
        self.sparse_search_provider.clear()
        self._indexed_ids.clear()
        rows = (
            db.query(KnowledgeRecord)
            .filter(KnowledgeRecord.index_version == self.index_version)
            .order_by(KnowledgeRecord.created_at.asc())
            .all()
        )
        indexed = 0
        failed = 0
        for row in rows:
            try:
                self._index_row_into_providers(row)
                indexed += 1
            except Exception:
                failed += 1
        self._cache_loaded = True
        return {"indexed": indexed, "failed": failed, "total": len(rows)}

    def _ensure_cache(self, *, db: Session) -> None:
        if self._cache_loaded:
            return
        self.rebuild_from_canonical(db=db)

    def _index_row_into_providers(self, row: KnowledgeRecord) -> None:
        if str(row.record_id) in self._indexed_ids:
            return
        vectors = self.embedding_provider.embed([str(row.text or "")])
        if not vectors:
            raise RuntimeError("embedding provider returned empty vector")
        vector = vectors[0]
        self.vector_index_provider.upsert(
            record_id=str(row.record_id),
            vector=vector,
            metadata={
                "tenant_id": str(row.tenant_id),
                "project_id": str(row.project_id or ""),
                "file_id": str(row.file_id or ""),
                "source_type": str(row.source_type),
            },
        )
        self.sparse_search_provider.upsert(record_id=str(row.record_id), text=str(row.text or ""))
        self._indexed_ids.add(str(row.record_id))

    def _apply_record(
        self,
        *,
        db: Session,
        record: CanonicalKnowledgeRecord,
        job: KnowledgeIndexJob | None = None,
    ) -> tuple[str, str]:
        existing = (
            db.query(KnowledgeRecord)
            .filter(
                KnowledgeRecord.tenant_id == _safe_int(record.tenant_id, 0),
                KnowledgeRecord.source_ref == str(record.source_ref),
                KnowledgeRecord.hash_sha256 == str(record.hash_sha256),
                KnowledgeRecord.index_version == str(record.index_version),
            )
            .first()
        )
        if existing is not None:
            if job is not None:
                job.status = INDEX_STATUS_SKIPPED
                job.failure_code = None
                job.error_detail = None
                job.updated_at = _now()
            return INDEX_STATUS_SKIPPED, ""

        row = KnowledgeRecord(
            record_id=str(record.record_id),
            tenant_id=_safe_int(record.tenant_id, 0),
            project_id=str(record.project_id) if record.project_id else None,
            file_id=str(record.file_id) if record.file_id else None,
            source_type=str(record.source_type),
            source_subtype=str(record.source_subtype),
            source_ref=str(record.source_ref),
            title=str(record.title),
            summary=str(record.summary),
            text=str(record.text),
            metadata_json=sanitize_public_payload(record.metadata),
            tags_json=[str(item) for item in _as_list(record.tags)],
            security_class=str(record.security_class or "internal"),
            hash_sha256=str(record.hash_sha256),
            index_version=str(record.index_version),
            embedding_status=INDEX_STATUS_PENDING,
            created_at=_now(),
            updated_at=_now(),
        )
        db.add(row)
        db.flush()
        try:
            self._index_row_into_providers(row)
            row.embedding_status = INDEX_STATUS_INDEXED
            row.updated_at = _now()
            db.add(row)
            if job is not None:
                job.status = INDEX_STATUS_INDEXED
                job.failure_code = None
                job.error_detail = None
                job.updated_at = _now()
            return INDEX_STATUS_INDEXED, ""
        except Exception as exc:
            row.embedding_status = INDEX_STATUS_FAILED
            row.updated_at = _now()
            db.add(row)
            if job is not None:
                job.status = INDEX_STATUS_FAILED
                job.failure_code = FAILURE_EMBEDDING_FAIL
                job.error_detail = str(exc)
                job.updated_at = _now()
            return INDEX_STATUS_FAILED, FAILURE_EMBEDDING_FAIL

    def _create_job(
        self,
        *,
        db: Session,
        event_id: str | None,
        event_type: str | None,
        tenant_id: str | None,
        project_id: str | None,
        file_id: str | None,
        source_ref: str | None,
        payload_json: dict[str, Any] | None,
    ) -> KnowledgeIndexJob:
        job = KnowledgeIndexJob(
            event_id=str(event_id) if event_id else None,
            event_type=str(event_type) if event_type else None,
            tenant_id=_safe_int(tenant_id, 0) if tenant_id is not None else None,
            project_id=str(project_id) if project_id else None,
            file_id=str(file_id) if file_id else None,
            source_ref=str(source_ref) if source_ref else None,
            status=INDEX_STATUS_PENDING,
            payload_json=sanitize_public_payload(payload_json or {}),
            retry_count=0,
            created_at=_now(),
            updated_at=_now(),
        )
        db.add(job)
        db.flush()
        return job

    def _mark_job_failure(self, *, job: KnowledgeIndexJob, failure_code: str, detail: str | None) -> None:
        job.status = INDEX_STATUS_FAILED
        job.failure_code = str(failure_code)
        job.error_detail = str(detail or "")[:2000]
        job.updated_at = _now()

    def _is_event_processed(self, *, db: Session, event_id: str, consumer: str) -> bool:
        existing = (
            db.query(ProcessedEventId)
            .filter(
                ProcessedEventId.event_id == str(event_id),
                ProcessedEventId.consumer == str(consumer),
            )
            .first()
        )
        return existing is not None

    def _mark_event_processed(self, *, db: Session, envelope: EventEnvelope, consumer: str, file_id: str | None) -> None:
        row = ProcessedEventId(
            event_id=str(envelope.id),
            event_type=str(envelope.type),
            consumer=str(consumer),
            file_id=str(file_id) if file_id else None,
            version_no=_safe_int((envelope.data or {}).get("version_no"), 1),
            trace_id=str(envelope.trace_id),
            payload=sanitize_public_payload(envelope.to_dict()),
        )
        db.add(row)

    def _project_id_for_file(self, file_row: UploadFile) -> str:
        meta = file_row.meta if isinstance(file_row.meta, dict) else {}
        return str(meta.get("project_id") or "default")

    def _decision_record(self, *, file_row: UploadFile) -> CanonicalKnowledgeRecord | None:
        payload = file_row.decision_json if isinstance(file_row.decision_json, dict) else {}
        if not payload:
            return None
        normalized = normalize_decision_json(payload)
        return canonical_record(
            tenant_id=str(file_row.tenant_id),
            project_id=self._project_id_for_file(file_row),
            file_id=str(file_row.file_id),
            source_type="database",
            source_subtype="decision_json",
            source_ref=f"scx://files/{file_row.file_id}/decision_json",
            title=normalized["title"],
            text=normalized["text"],
            metadata={
                **normalized["metadata"],
                "file_id": str(file_row.file_id),
                "status": str(file_row.status or ""),
            },
            tags=normalized["tags"],
            index_version=self.index_version,
        )

    def _dfm_record(self, *, file_row: UploadFile) -> CanonicalKnowledgeRecord | None:
        meta = file_row.meta if isinstance(file_row.meta, dict) else {}
        payload = meta.get("dfm_report_json") if isinstance(meta.get("dfm_report_json"), dict) else {}
        if not payload:
            return None
        normalized = normalize_dfm_report(payload)
        return canonical_record(
            tenant_id=str(file_row.tenant_id),
            project_id=self._project_id_for_file(file_row),
            file_id=str(file_row.file_id),
            source_type="artifact",
            source_subtype="dfm_report",
            source_ref=f"scx://files/{file_row.file_id}/dfm_report",
            title=normalized["title"],
            text=normalized["text"],
            metadata={**normalized["metadata"], "file_id": str(file_row.file_id)},
            tags=normalized["tags"],
            index_version=self.index_version,
        )

    def _assembly_record(self, *, file_row: UploadFile) -> CanonicalKnowledgeRecord | None:
        meta = file_row.meta if isinstance(file_row.meta, dict) else {}
        payload = meta.get("assembly_meta") if isinstance(meta.get("assembly_meta"), dict) else {}
        if not payload:
            return None
        normalized = normalize_assembly_meta(payload)
        return canonical_record(
            tenant_id=str(file_row.tenant_id),
            project_id=self._project_id_for_file(file_row),
            file_id=str(file_row.file_id),
            source_type="artifact",
            source_subtype="assembly_meta",
            source_ref=f"scx://files/{file_row.file_id}/assembly_meta",
            title=normalized["title"],
            text=normalized["text"],
            metadata={**normalized["metadata"], "file_id": str(file_row.file_id)},
            tags=normalized["tags"],
            index_version=self.index_version,
        )

    def _package_record(self, *, file_row: UploadFile) -> CanonicalKnowledgeRecord | None:
        meta = file_row.meta if isinstance(file_row.meta, dict) else {}
        package_key = str(meta.get("production_package_key") or "").strip()
        if not package_key:
            return None
        payload = {
            "file_id": str(file_row.file_id),
            "status": str(file_row.status),
            "mode": str(meta.get("mode") or ""),
            "kind": str(meta.get("kind") or ""),
            "package_ready": bool(package_key),
        }
        return canonical_record(
            tenant_id=str(file_row.tenant_id),
            project_id=self._project_id_for_file(file_row),
            file_id=str(file_row.file_id),
            source_type="artifact",
            source_subtype="production_pack",
            source_ref=f"scx://files/{file_row.file_id}/production_package",
            title="Production package summary",
            text=json.dumps(payload, ensure_ascii=False, sort_keys=True),
            metadata=payload,
            tags=["production_pack", "artifact"],
            index_version=self.index_version,
        )

    def _error_record(self, *, file_row: UploadFile) -> CanonicalKnowledgeRecord | None:
        meta = file_row.meta if isinstance(file_row.meta, dict) else {}
        error_text = str(meta.get("error") or "").strip()
        error_code = str(meta.get("error_code") or "").strip()
        if not (error_text or error_code):
            return None
        payload = {"file_id": str(file_row.file_id), "error_code": error_code, "error": error_text}
        return canonical_record(
            tenant_id=str(file_row.tenant_id),
            project_id=self._project_id_for_file(file_row),
            file_id=str(file_row.file_id),
            source_type="artifact",
            source_subtype="error_report",
            source_ref=f"scx://files/{file_row.file_id}/error_report",
            title="Processing error report",
            text=json.dumps(payload, ensure_ascii=False, sort_keys=True),
            metadata=payload,
            tags=["error_report", "artifact"],
            index_version=self.index_version,
        )

    def _orchestrator_record(self, *, row: OrchestratorSession, tenant_id: str, project_id: str) -> CanonicalKnowledgeRecord:
        payload = row.decision_json if isinstance(row.decision_json, dict) else {}
        normalized = normalize_decision_json(payload)
        return canonical_record(
            tenant_id=tenant_id,
            project_id=project_id,
            file_id=str(row.file_id),
            source_type="database",
            source_subtype="orchestrator_session",
            source_ref=f"scx://orchestrator/sessions/{row.id}",
            title="Orchestrator session decision",
            text=normalized["text"],
            metadata={
                **normalized["metadata"],
                "session_id": str(row.id),
                "state": str(row.state),
                "status_gate": str(row.status_gate),
                "approval_required": bool(row.approval_required),
            },
            tags=["orchestrator", "decision_json"],
            index_version=self.index_version,
        )

    def _rule_config_record(self, *, row: RuleConfig, tenant_id: str, project_id: str) -> CanonicalKnowledgeRecord:
        normalized = normalize_rule_config(
            key=str(row.key),
            value_json=row.value_json if isinstance(row.value_json, dict) else {},
            updated_at=row.updated_at.isoformat() if row.updated_at else None,
        )
        return canonical_record(
            tenant_id=tenant_id,
            project_id=project_id,
            file_id=None,
            source_type="database",
            source_subtype="rule_configs",
            source_ref=f"scx://rule_configs/{row.key}",
            title=normalized["title"],
            text=normalized["text"],
            metadata=normalized["metadata"],
            tags=normalized["tags"],
            index_version=self.index_version,
        )

    def _audit_record(self, *, row: AuditEvent, tenant_id: str, project_id: str) -> CanonicalKnowledgeRecord:
        payload = {
            "id": str(row.id),
            "event_type": str(row.event_type),
            "actor_user_id": str(row.actor_user_id or ""),
            "actor_anon_sub": str(row.actor_anon_sub or ""),
            "file_id": str(row.file_id or ""),
            "created_at": row.created_at.isoformat() if row.created_at else "",
            "data": sanitize_public_payload(row.data if isinstance(row.data, dict) else {}),
        }
        normalized = normalize_audit_event(payload)
        source_subtype = "approvals" if str(row.event_type).startswith("approval.") else "audit_events"
        return canonical_record(
            tenant_id=tenant_id,
            project_id=project_id,
            file_id=str(row.file_id or "") or None,
            source_type="event",
            source_subtype=source_subtype,
            source_ref=f"scx://audit/{row.id}",
            title=normalized["title"],
            text=normalized["text"],
            metadata={**normalized["metadata"], "raw_event_type": str(row.event_type)},
            tags=normalized["tags"],
            index_version=self.index_version,
        )

    def _document_records(
        self,
        *,
        tenant_id: str,
        project_id: str,
        document_paths: list[str] | None = None,
    ) -> list[CanonicalKnowledgeRecord]:
        records: list[CanonicalKnowledgeRecord] = []
        paths: list[Path] = []
        if document_paths:
            for item in document_paths:
                path = Path(item)
                if not path.is_absolute():
                    path = (_WORKSPACE_ROOT / path).resolve()
                if path.exists() and path.is_file():
                    paths.append(path)
        else:
            for pattern in _DEFAULT_DOC_PATTERNS:
                for path in sorted(_WORKSPACE_ROOT.glob(pattern)):
                    if path.is_file():
                        paths.append(path.resolve())
        for path in paths:
            try:
                raw = path.read_text(encoding="utf-8", errors="ignore")
                normalized = normalize_document(path=str(path.relative_to(_WORKSPACE_ROOT)), content=raw)
            except Exception:
                continue
            records.append(
                canonical_record(
                    tenant_id=tenant_id,
                    project_id=project_id,
                    file_id=None,
                    source_type="document",
                    source_subtype="markdown",
                    source_ref=f"scx://docs/{path.relative_to(_WORKSPACE_ROOT)}",
                    title=normalized["title"],
                    text=normalized["text"],
                    metadata=normalized["metadata"],
                    tags=normalized["tags"],
                    index_version=self.index_version,
                )
            )
        return records

    def index_scope(
        self,
        *,
        db: Session,
        tenant_id: str,
        project_id: str,
        file_id: str | None = None,
        source_types: list[str] | None = None,
        document_paths: list[str] | None = None,
        include_events: bool = True,
    ) -> dict[str, Any]:
        wanted = {str(item).strip().lower() for item in _as_list(source_types) if str(item).strip()}

        def _enabled(name: str, group: str) -> bool:
            if not wanted:
                return True
            return name in wanted or group in wanted

        file_rows_query = db.query(UploadFile).filter(UploadFile.tenant_id == _safe_int(tenant_id, 0))
        if file_id:
            file_rows_query = file_rows_query.filter(UploadFile.file_id == str(file_id))
        file_rows = file_rows_query.order_by(UploadFile.updated_at.desc()).all()
        records: list[CanonicalKnowledgeRecord] = []

        if _enabled("decision_json", "database") or _enabled("artifacts", "artifacts"):
            for row in file_rows:
                if _enabled("decision_json", "database"):
                    decision = self._decision_record(file_row=row)
                    if decision is not None:
                        records.append(decision)
                if _enabled("dfm_report", "artifacts"):
                    dfm = self._dfm_record(file_row=row)
                    if dfm is not None:
                        records.append(dfm)
                if _enabled("assembly_meta", "artifacts"):
                    assembly = self._assembly_record(file_row=row)
                    if assembly is not None:
                        records.append(assembly)
                if _enabled("production_pack", "artifacts"):
                    pack = self._package_record(file_row=row)
                    if pack is not None:
                        records.append(pack)
                if _enabled("error_report", "artifacts"):
                    err = self._error_record(file_row=row)
                    if err is not None:
                        records.append(err)

        if _enabled("orchestrator_sessions", "database"):
            session_query = db.query(OrchestratorSession)
            if file_id:
                session_query = session_query.filter(OrchestratorSession.file_id == str(file_id))
            for row in session_query.all():
                records.append(self._orchestrator_record(row=row, tenant_id=tenant_id, project_id=project_id))

        if _enabled("rule_configs", "database"):
            for row in db.query(RuleConfig).all():
                records.append(self._rule_config_record(row=row, tenant_id=tenant_id, project_id=project_id))

        if _enabled("projects", "database"):
            for row in db.query(Project).all():
                payload = {
                    "project_id": str(row.id),
                    "name": str(row.name),
                    "privacy": str(row.privacy),
                    "owner_id": str(row.owner_id or ""),
                }
                records.append(
                    canonical_record(
                        tenant_id=tenant_id,
                        project_id=project_id,
                        file_id=None,
                        source_type="database",
                        source_subtype="projects",
                        source_ref=f"scx://projects/{row.id}",
                        title=f"Project {row.name}",
                        text=json.dumps(payload, ensure_ascii=False, sort_keys=True),
                        metadata=payload,
                        tags=["projects", "database"],
                        index_version=self.index_version,
                    )
                )

        if _enabled("files", "database"):
            file_registry_query = db.query(FileRegistry)
            if file_id:
                file_registry_query = file_registry_query.filter(FileRegistry.file_id == str(file_id))
            for row in file_registry_query.all():
                payload = {
                    "id": str(row.id),
                    "file_id": str(row.file_id),
                    "uploaded_file_id": str(row.uploaded_file_id or ""),
                }
                records.append(
                    canonical_record(
                        tenant_id=tenant_id,
                        project_id=project_id,
                        file_id=str(row.file_id),
                        source_type="database",
                        source_subtype="files",
                        source_ref=f"scx://files_registry/{row.id}",
                        title=f"File registry {row.file_id}",
                        text=json.dumps(payload, ensure_ascii=False, sort_keys=True),
                        metadata=payload,
                        tags=["files", "database"],
                        index_version=self.index_version,
                    )
                )

        if _enabled("file_versions", "database"):
            version_query = db.query(FileVersion)
            if file_id:
                version_query = version_query.filter(FileVersion.file_id == str(file_id))
            for row in version_query.all():
                payload = {
                    "id": _safe_int(row.id),
                    "file_id": str(row.file_id),
                    "version_no": _safe_int(row.version_no, 1),
                    "uploaded_file_id": str(row.uploaded_file_id or ""),
                }
                records.append(
                    canonical_record(
                        tenant_id=tenant_id,
                        project_id=project_id,
                        file_id=str(row.file_id),
                        source_type="database",
                        source_subtype="file_versions",
                        source_ref=f"scx://file_versions/{row.id}",
                        title=f"File version {row.file_id} v{row.version_no}",
                        text=json.dumps(payload, ensure_ascii=False, sort_keys=True),
                        metadata=payload,
                        tags=["file_versions", "database"],
                        index_version=self.index_version,
                    )
                )

        if _enabled("jobs", "database"):
            for row in db.query(Job).all():
                payload = {
                    "job_id": str(row.id),
                    "type": str(row.type),
                    "status": str(row.status),
                    "queue": str(row.queue),
                    "error": str(row.error or ""),
                    "revision_id": str(row.rev_uid),
                }
                records.append(
                    canonical_record(
                        tenant_id=tenant_id,
                        project_id=project_id,
                        file_id=None,
                        source_type="database",
                        source_subtype="jobs",
                        source_ref=f"scx://jobs/{row.id}",
                        title=f"Job {row.id}",
                        text=json.dumps(payload, ensure_ascii=False, sort_keys=True),
                        metadata=payload,
                        tags=["jobs", "database"],
                        index_version=self.index_version,
                    )
                )

        if _enabled("job_logs", "database"):
            job_log_query = db.query(JobLog)
            if file_id:
                job_log_query = job_log_query.filter(JobLog.file_id == str(file_id))
            for row in job_log_query.order_by(JobLog.created_at.desc()).limit(400).all():
                payload = {
                    "job_id": str(row.job_id or ""),
                    "file_id": str(row.file_id or ""),
                    "stage": str(row.stage or ""),
                    "message": str(row.message or ""),
                    "payload": sanitize_public_payload(row.payload if isinstance(row.payload, dict) else {}),
                }
                records.append(
                    canonical_record(
                        tenant_id=tenant_id,
                        project_id=project_id,
                        file_id=str(row.file_id or "") or None,
                        source_type="database",
                        source_subtype="job_logs",
                        source_ref=f"scx://job_logs/{row.id}",
                        title=f"Job log {row.id}",
                        text=json.dumps(payload, ensure_ascii=False, sort_keys=True),
                        metadata=payload,
                        tags=["job_logs", "database"],
                        index_version=self.index_version,
                    )
                )

        if include_events and _enabled("audit_events", "events"):
            audit_query = db.query(AuditEvent).order_by(AuditEvent.created_at.desc())
            if file_id:
                audit_query = audit_query.filter(AuditEvent.file_id == str(file_id))
            for row in audit_query.limit(600).all():
                records.append(self._audit_record(row=row, tenant_id=tenant_id, project_id=project_id))

        if _enabled("documents", "documents"):
            records.extend(
                self._document_records(
                    tenant_id=tenant_id,
                    project_id=project_id,
                    document_paths=document_paths,
                )
            )

        indexed = 0
        skipped = 0
        failed = 0
        for record in records:
            status, _failure = self._apply_record(db=db, record=record, job=None)
            if status == INDEX_STATUS_INDEXED:
                indexed += 1
            elif status == INDEX_STATUS_SKIPPED:
                skipped += 1
            else:
                failed += 1
        self._cache_loaded = False
        return {
            "status": "ok",
            "tenant_id": str(tenant_id),
            "project_id": str(project_id),
            "file_id": str(file_id) if file_id else None,
            "indexed": indexed,
            "skipped": skipped,
            "failed": failed,
            "total": len(records),
        }

    def reindex_scope(
        self,
        *,
        db: Session,
        tenant_id: str,
        project_id: str,
        file_id: str | None = None,
        source_types: list[str] | None = None,
        document_paths: list[str] | None = None,
    ) -> dict[str, Any]:
        query = db.query(KnowledgeRecord).filter(
            KnowledgeRecord.tenant_id == _safe_int(tenant_id, 0),
            KnowledgeRecord.index_version == self.index_version,
        )
        if project_id:
            query = query.filter(KnowledgeRecord.project_id == str(project_id))
        if file_id:
            query = query.filter(KnowledgeRecord.file_id == str(file_id))
        deleted = query.delete(synchronize_session=False)
        self.vector_index_provider.clear()
        self.sparse_search_provider.clear()
        self._indexed_ids.clear()
        self._cache_loaded = False
        indexed_summary = self.index_scope(
            db=db,
            tenant_id=tenant_id,
            project_id=project_id,
            file_id=file_id,
            source_types=source_types,
            document_paths=document_paths,
            include_events=True,
        )
        indexed_summary["deleted"] = int(deleted)
        indexed_summary["reindexed"] = True
        return indexed_summary

    def ingest_event(self, *, db: Session, envelope: EventEnvelope) -> dict[str, Any]:
        if not isinstance(envelope, EventEnvelope):
            raise ValueError("invalid event envelope")
        if envelope.type not in _TRIGGER_EVENTS:
            return {"status": "ignored", "event_type": envelope.type}

        file_id = str((envelope.data or {}).get("file_id") or envelope.subject or "").strip() or None
        consumer = "knowledge.ingestion"
        if self._is_event_processed(db=db, event_id=envelope.id, consumer=consumer):
            return {"status": INDEX_STATUS_SKIPPED, "event_id": envelope.id, "reason": "duplicate_event"}

        job = self._create_job(
            db=db,
            event_id=envelope.id,
            event_type=envelope.type,
            tenant_id=envelope.tenant_id,
            project_id=envelope.project_id,
            file_id=file_id,
            source_ref=f"event://{envelope.type}/{envelope.id}",
            payload_json=envelope.to_dict(),
        )
        indexed = 0
        skipped = 0
        failed = 0
        produced: list[str] = []

        try:
            records = self._records_from_event(db=db, envelope=envelope, file_id=file_id)
            if not records:
                job.status = INDEX_STATUS_SKIPPED
                job.updated_at = _now()
                db.add(job)
                self._mark_event_processed(db=db, envelope=envelope, consumer=consumer, file_id=file_id)
                _append_worker_log(
                    {
                        "event_id": envelope.id,
                        "event_type": envelope.type,
                        "status": INDEX_STATUS_SKIPPED,
                        "reason": "no_records",
                    }
                )
                return {"status": INDEX_STATUS_SKIPPED, "event_id": envelope.id, "indexed": 0, "skipped": 0, "failed": 0}

            for record in records:
                status, _failure = self._apply_record(db=db, record=record, job=job)
                produced.append(record.record_id)
                if status == INDEX_STATUS_INDEXED:
                    indexed += 1
                elif status == INDEX_STATUS_SKIPPED:
                    skipped += 1
                else:
                    failed += 1
            if failed > 0 and indexed == 0:
                self._mark_job_failure(job=job, failure_code=FAILURE_INDEX_WRITE_FAIL, detail="all records failed")
            elif indexed > 0:
                job.status = INDEX_STATUS_INDEXED
                job.updated_at = _now()
            else:
                job.status = INDEX_STATUS_SKIPPED
                job.updated_at = _now()
            self._mark_event_processed(db=db, envelope=envelope, consumer=consumer, file_id=file_id)
            self._cache_loaded = False
            _append_worker_log(
                {
                    "event_id": envelope.id,
                    "event_type": envelope.type,
                    "status": str(job.status),
                    "indexed": indexed,
                    "skipped": skipped,
                    "failed": failed,
                    "record_ids": produced,
                }
            )
            return {
                "status": str(job.status),
                "event_id": envelope.id,
                "indexed": indexed,
                "skipped": skipped,
                "failed": failed,
                "record_ids": produced,
            }
        except ValueError as exc:
            self._mark_job_failure(job=job, failure_code=FAILURE_INVALID_PAYLOAD, detail=str(exc))
            _append_worker_log(
                {
                    "event_id": envelope.id,
                    "event_type": envelope.type,
                    "status": INDEX_STATUS_FAILED,
                    "failure_code": FAILURE_INVALID_PAYLOAD,
                    "error": str(exc),
                }
            )
            return {"status": INDEX_STATUS_FAILED, "event_id": envelope.id, "failure_code": FAILURE_INVALID_PAYLOAD}
        except LookupError as exc:
            self._mark_job_failure(job=job, failure_code=FAILURE_SOURCE_NOT_FOUND, detail=str(exc))
            _append_worker_log(
                {
                    "event_id": envelope.id,
                    "event_type": envelope.type,
                    "status": INDEX_STATUS_FAILED,
                    "failure_code": FAILURE_SOURCE_NOT_FOUND,
                    "error": str(exc),
                }
            )
            return {"status": INDEX_STATUS_FAILED, "event_id": envelope.id, "failure_code": FAILURE_SOURCE_NOT_FOUND}
        except Exception as exc:
            failure_code = FAILURE_NORMALIZATION_FAIL if isinstance(exc, RuntimeError) else FAILURE_INDEX_WRITE_FAIL
            self._mark_job_failure(job=job, failure_code=failure_code, detail=str(exc))
            _append_worker_log(
                {
                    "event_id": envelope.id,
                    "event_type": envelope.type,
                    "status": INDEX_STATUS_FAILED,
                    "failure_code": failure_code,
                    "error": str(exc),
                }
            )
            return {"status": INDEX_STATUS_FAILED, "event_id": envelope.id, "failure_code": failure_code}

    def _records_from_event(
        self,
        *,
        db: Session,
        envelope: EventEnvelope,
        file_id: str | None,
    ) -> list[CanonicalKnowledgeRecord]:
        records: list[CanonicalKnowledgeRecord] = []
        event_type = str(envelope.type)

        if event_type in {"audit.logged"}:
            audit_payload = {
                "id": str((envelope.data or {}).get("audit_id") or envelope.id),
                "event_type": str((envelope.data or {}).get("event_type") or "audit.logged"),
                "actor_user_id": str((envelope.data or {}).get("actor_user_id") or ""),
                "actor_anon_sub": str((envelope.data or {}).get("actor_anon_sub") or ""),
                "file_id": str((envelope.data or {}).get("file_id") or file_id or ""),
                "timestamp": str((envelope.data or {}).get("timestamp") or envelope.time),
            }
            normalized = normalize_audit_event(audit_payload)
            records.append(
                canonical_record(
                    tenant_id=str(envelope.tenant_id),
                    project_id=str(envelope.project_id),
                    file_id=str(audit_payload.get("file_id") or "") or None,
                    source_type="event",
                    source_subtype="audit_events",
                    source_ref=f"event://audit/{audit_payload['id']}",
                    title=normalized["title"],
                    text=normalized["text"],
                    metadata=normalized["metadata"],
                    tags=normalized["tags"],
                    index_version=self.index_version,
                )
            )
            return records

        if event_type == "document.imported":
            paths = [str(item) for item in _as_list((envelope.data or {}).get("paths")) if str(item).strip()]
            return self._document_records(
                tenant_id=str(envelope.tenant_id),
                project_id=str(envelope.project_id),
                document_paths=paths or None,
            )

        if not file_id:
            raise ValueError("event payload missing file_id")
        file_row = db.query(UploadFile).filter(UploadFile.file_id == str(file_id)).first()
        if file_row is None:
            raise LookupError(f"source file not found: {file_id}")
        if str(file_row.tenant_id) != str(envelope.tenant_id):
            raise ValueError("tenant scope mismatch")

        if event_type in {"decision.produced", "decision.ready"}:
            decision = self._decision_record(file_row=file_row)
            if decision is not None:
                records.append(decision)
            session = db.query(OrchestratorSession).filter(OrchestratorSession.file_id == str(file_id)).first()
            if session is not None:
                records.append(
                    self._orchestrator_record(
                        row=session,
                        tenant_id=str(envelope.tenant_id),
                        project_id=str(envelope.project_id),
                    )
                )
            return records

        if event_type in {"dfm.completed", "dfm.ready"}:
            dfm = self._dfm_record(file_row=file_row)
            if dfm is not None:
                records.append(dfm)
            return records

        if event_type in {"assembly.ready"}:
            assembly = self._assembly_record(file_row=file_row)
            if assembly is not None:
                records.append(assembly)
            return records

        if event_type in {"file.ready", "package.ready"}:
            for producer in (self._decision_record, self._dfm_record, self._assembly_record, self._package_record, self._error_record):
                item = producer(file_row=file_row)
                if item is not None:
                    records.append(item)
            return records

        if event_type in _APPROVAL_EVENTS:
            session = db.query(OrchestratorSession).filter(OrchestratorSession.file_id == str(file_id)).first()
            if session is not None:
                records.append(
                    self._orchestrator_record(
                        row=session,
                        tenant_id=str(envelope.tenant_id),
                        project_id=str(envelope.project_id),
                    )
                )
            approval_payload = {
                "id": str(envelope.id),
                "event_type": str(envelope.type),
                "actor_user_id": str((envelope.data or {}).get("actor_user_id") or ""),
                "actor_anon_sub": str((envelope.data or {}).get("actor_anon_sub") or ""),
                "file_id": str(file_id),
                "timestamp": str(envelope.time),
            }
            normalized = normalize_audit_event(approval_payload)
            records.append(
                canonical_record(
                    tenant_id=str(envelope.tenant_id),
                    project_id=str(envelope.project_id),
                    file_id=str(file_id),
                    source_type="event",
                    source_subtype="approvals",
                    source_ref=f"event://approvals/{envelope.id}",
                    title=normalized["title"],
                    text=normalized["text"],
                    metadata=normalized["metadata"],
                    tags=normalized["tags"] + ["approval_event"],
                    index_version=self.index_version,
                )
            )
            return records

        return records

    def search_knowledge(
        self,
        *,
        db: Session,
        query: str,
        tenant_id: str,
        project_id: str | None = None,
        file_id: str | None = None,
        top_k: int = 6,
        source_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        query_text = str(query or "").strip()
        if not query_text:
            return []
        self._ensure_cache(db=db)
        rows_query = db.query(KnowledgeRecord).filter(
            KnowledgeRecord.tenant_id == _safe_int(tenant_id, 0),
            KnowledgeRecord.index_version == self.index_version,
        )
        if project_id:
            rows_query = rows_query.filter(KnowledgeRecord.project_id == str(project_id))
        if file_id:
            rows_query = rows_query.filter(KnowledgeRecord.file_id == str(file_id))
        wanted_sources = {str(item).strip().lower() for item in _as_list(source_types) if str(item).strip()}
        if wanted_sources:
            rows_query = rows_query.filter(KnowledgeRecord.source_type.in_(sorted(wanted_sources)))
        rows = rows_query.all()
        if not rows:
            return []

        for row in rows:
            if str(row.record_id) not in self._indexed_ids:
                try:
                    self._index_row_into_providers(row)
                except Exception:
                    continue

        allowed_ids = {str(row.record_id) for row in rows}
        query_vector = self.embedding_provider.embed([query_text])[0]
        dense = dict(self.vector_index_provider.search(query_vector=query_vector, top_k=max(16, top_k * 6), allowed_ids=allowed_ids))
        sparse = dict(self.sparse_search_provider.search(query=query_text, top_k=max(16, top_k * 6), allowed_ids=allowed_ids))
        max_dense = max(dense.values()) if dense else 1.0
        max_sparse = max(sparse.values()) if sparse else 1.0
        row_by_id = {str(row.record_id): row for row in rows}

        scored: list[tuple[str, float]] = []
        for rid in allowed_ids:
            dense_score = dense.get(rid, 0.0) / max_dense if max_dense > 0 else 0.0
            sparse_score = sparse.get(rid, 0.0) / max_sparse if max_sparse > 0 else 0.0
            final_score = (0.65 * dense_score) + (0.35 * sparse_score)
            if final_score <= 0:
                continue
            scored.append((rid, final_score))
        scored.sort(key=lambda item: item[1], reverse=True)

        results: list[dict[str, Any]] = []
        for rid, score in scored[: max(1, int(top_k))]:
            row = row_by_id.get(rid)
            if row is None:
                continue
            results.append(
                {
                    "record_id": str(row.record_id),
                    "score": round(float(score), 6),
                    "title": str(row.title),
                    "text": str(row.text),
                    "summary": str(row.summary),
                    "metadata": sanitize_public_payload(row.metadata_json if isinstance(row.metadata_json, dict) else {}),
                    "source_ref": str(row.source_ref),
                    "source_type": str(row.source_type),
                    "source_subtype": str(row.source_subtype),
                    "file_id": str(row.file_id) if row.file_id else None,
                }
            )
        return results

    def get_context_bundle(
        self,
        *,
        db: Session,
        query: str,
        tenant_id: str,
        project_id: str | None = None,
        file_id: str | None = None,
        top_k: int = 6,
        source_types: list[str] | None = None,
    ) -> dict[str, Any]:
        results = self.search_knowledge(
            db=db,
            query=query,
            tenant_id=tenant_id,
            project_id=project_id,
            file_id=file_id,
            top_k=top_k,
            source_types=source_types,
        )
        return {
            "query": str(query),
            "tenant_id": str(tenant_id),
            "project_id": str(project_id) if project_id else None,
            "file_id": str(file_id) if file_id else None,
            "relevant_records": results,
            "source_references": [item["source_ref"] for item in results],
            "provenance": [
                {
                    "record_id": item["record_id"],
                    "source_ref": item["source_ref"],
                    "source_type": item["source_type"],
                    "source_subtype": item["source_subtype"],
                }
                for item in results
            ],
        }

    def get_record(self, *, db: Session, record_id: str, tenant_id: str) -> dict[str, Any] | None:
        row = (
            db.query(KnowledgeRecord)
            .filter(
                KnowledgeRecord.record_id == str(record_id),
                KnowledgeRecord.tenant_id == _safe_int(tenant_id, 0),
                KnowledgeRecord.index_version == self.index_version,
            )
            .first()
        )
        if row is None:
            return None
        return {
            "record_id": str(row.record_id),
            "tenant_id": str(row.tenant_id),
            "project_id": str(row.project_id) if row.project_id else None,
            "file_id": str(row.file_id) if row.file_id else None,
            "source_type": str(row.source_type),
            "source_subtype": str(row.source_subtype),
            "source_ref": str(row.source_ref),
            "title": str(row.title),
            "summary": str(row.summary),
            "text": str(row.text),
            "metadata": sanitize_public_payload(row.metadata_json if isinstance(row.metadata_json, dict) else {}),
            "tags": [str(item) for item in _as_list(row.tags_json)],
            "security_class": str(row.security_class),
            "hash_sha256": str(row.hash_sha256),
            "index_version": str(row.index_version),
            "embedding_status": str(row.embedding_status),
            "created_at": row.created_at.isoformat() if row.created_at else None,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }


@lru_cache(maxsize=1)
def get_knowledge_service() -> KnowledgeService:
    return KnowledgeService()
