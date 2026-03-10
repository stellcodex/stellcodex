from __future__ import annotations

from typing import Any
from sqlalchemy.orm import Session
from app.retrieval.hybrid import HybridRetrievalResult, hybrid_search


class KnowledgeRetriever:
    """High-level retriever interface used by Agent OS components."""

    def retrieve(
        self,
        db: Session,
        *,
        query: str,
        tenant_id: str,
        project_id: str = "default",
        file_id: str | None = None,
        top_k: int = 6,
        source_types: list[str] | None = None,
    ) -> HybridRetrievalResult:
        return hybrid_search(
            db,
            query=query,
            tenant_id=tenant_id,
            project_id=project_id,
            file_id=file_id,
            top_k=top_k,
            source_types=source_types,
        )
