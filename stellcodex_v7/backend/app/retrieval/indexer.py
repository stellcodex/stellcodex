from __future__ import annotations
from typing import Any
from sqlalchemy.orm import Session
from app.core.events import EventEnvelope


def index_event(db: Session, envelope: EventEnvelope) -> dict[str, Any]:
    """Index an event envelope into knowledge records. Delegates to knowledge service."""
    from app.knowledge.service import get_knowledge_service
    svc = get_knowledge_service()
    result = svc.ingest_event(db=db, envelope=envelope)
    return result


def index_scope(
    db: Session,
    *,
    tenant_id: str,
    project_id: str = "default",
    file_id: str | None = None,
    source_types: list[str] | None = None,
) -> dict[str, Any]:
    """Index all available records for a scope. Delegates to knowledge service."""
    from app.knowledge.service import get_knowledge_service
    svc = get_knowledge_service()
    return svc.index_scope(
        db=db,
        tenant_id=tenant_id,
        project_id=project_id,
        file_id=file_id,
        source_types=source_types or [],
        document_paths=[],
        include_events=True,
    )
