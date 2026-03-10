"""Knowledge record access layer — wraps knowledge service for Agent OS."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeRecord


def get_record_by_id(db: Session, record_id: str, tenant_id: str | None = None) -> dict[str, Any] | None:
    q = db.query(KnowledgeRecord).filter(KnowledgeRecord.record_id == record_id)
    if tenant_id:
        try:
            q = q.filter(KnowledgeRecord.tenant_id == int(tenant_id))
        except (ValueError, TypeError):
            pass
    row = q.first()
    if row is None:
        return None
    return _to_dict(row)


def list_records(
    db: Session,
    *,
    tenant_id: str,
    project_id: str | None = None,
    source_type: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    try:
        tid = int(tenant_id)
    except (ValueError, TypeError):
        return []
    q = db.query(KnowledgeRecord).filter(KnowledgeRecord.tenant_id == tid)
    if project_id:
        q = q.filter(KnowledgeRecord.project_id == project_id)
    if source_type:
        q = q.filter(KnowledgeRecord.source_type == source_type)
    rows = q.order_by(KnowledgeRecord.created_at.desc()).limit(max(1, min(limit, 200))).all()
    return [_to_dict(r) for r in rows]


def _to_dict(row: KnowledgeRecord) -> dict[str, Any]:
    return {
        "record_id": row.record_id,
        "tenant_id": str(row.tenant_id),
        "project_id": row.project_id,
        "file_id": row.file_id,
        "source_type": row.source_type,
        "source_ref": row.source_ref,
        "title": row.title,
        "summary": row.summary,
        "hash_sha256": row.hash_sha256,
        "embedding_status": row.embedding_status,
        "created_at": str(row.created_at),
    }
