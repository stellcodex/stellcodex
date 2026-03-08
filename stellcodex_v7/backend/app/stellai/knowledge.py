from __future__ import annotations

from sqlalchemy.orm import Session

from app.knowledge.service import get_knowledge_service
from app.stellai.types import RuntimeContext


def search_knowledge(
    *,
    db: Session,
    context: RuntimeContext,
    query: str,
    top_k: int = 6,
    source_types: list[str] | None = None,
) -> list[dict]:
    service = get_knowledge_service()
    return service.search_knowledge(
        db=db,
        query=query,
        tenant_id=context.tenant_id,
        project_id=context.project_id,
        file_id=context.file_ids[0] if context.file_ids else None,
        top_k=top_k,
        source_types=source_types,
    )


def get_context_bundle(
    *,
    db: Session,
    context: RuntimeContext,
    query: str,
    top_k: int = 6,
    source_types: list[str] | None = None,
) -> dict:
    service = get_knowledge_service()
    return service.get_context_bundle(
        db=db,
        query=query,
        tenant_id=context.tenant_id,
        project_id=context.project_id,
        file_id=context.file_ids[0] if context.file_ids else None,
        top_k=top_k,
        source_types=source_types,
    )
