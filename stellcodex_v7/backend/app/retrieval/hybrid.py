"""Hybrid retrieval — vector + BM25 combined scoring.

Wraps the existing knowledge service. Does NOT reinvent BM25 or vector search;
delegates to knowledge/providers.py which already handles this.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session


@dataclass
class RetrievalHit:
    record_id: str
    score: float
    title: str
    text: str
    source_ref: str
    source_uri: str
    hash_sha256: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HybridRetrievalResult:
    query: str
    tenant_id: str
    hits: list[RetrievalHit] = field(default_factory=list)
    top_score: float = 0.0
    total_records_searched: int = 0

    @property
    def citations(self) -> list[dict[str, Any]]:
        return [
            {"source_uri": h.source_uri, "hash": h.hash_sha256, "score": h.score, "title": h.title}
            for h in self.hits
        ]


def hybrid_search(
    db: Session,
    *,
    query: str,
    tenant_id: str,
    project_id: str = "default",
    file_id: str | None = None,
    top_k: int = 6,
    source_types: list[str] | None = None,
) -> HybridRetrievalResult:
    """Perform hybrid knowledge retrieval. Delegates to knowledge service."""
    from app.knowledge.service import get_knowledge_service
    from app.models.knowledge import KnowledgeRecord

    svc = get_knowledge_service()
    raw_results = svc.search_knowledge(
        db=db,
        query=query,
        tenant_id=tenant_id,
        project_id=project_id,
        file_id=file_id,
        top_k=top_k,
        source_types=source_types or [],
    )

    total = db.query(KnowledgeRecord).filter(
        KnowledgeRecord.tenant_id == int(tenant_id) if tenant_id.isdigit() else KnowledgeRecord.tenant_id == tenant_id
    ).count() if tenant_id else 0

    hits = [
        RetrievalHit(
            record_id=r.get("record_id", ""),
            score=float(r.get("score", 0.0)),
            title=r.get("title", ""),
            text=(r.get("text") or "")[:1000],
            source_ref=r.get("source_ref", ""),
            source_uri=r.get("source_ref", ""),
            hash_sha256=r.get("metadata", {}).get("hash_sha256", ""),
            metadata=r.get("metadata", {}),
        )
        for r in raw_results
    ]

    top_score = max((h.score for h in hits), default=0.0)
    return HybridRetrievalResult(
        query=query,
        tenant_id=tenant_id,
        hits=hits,
        top_score=top_score,
        total_records_searched=total,
    )
