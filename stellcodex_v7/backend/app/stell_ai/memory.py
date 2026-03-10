"""Memory — retrieval-augmented context for Agent OS.

Connects to Knowledge Engine for hybrid retrieval.
Never fabricates knowledge — all results cite source_uri + hash.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from app.retrieval.hybrid import HybridRetrievalResult, hybrid_search


@dataclass
class MemoryContext:
    query: str
    tenant_id: str
    hits: list[dict[str, Any]] = field(default_factory=list)
    citations: list[dict[str, Any]] = field(default_factory=list)
    top_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "tenant_id": self.tenant_id,
            "hit_count": len(self.hits),
            "top_score": self.top_score,
            "citations": self.citations,
        }


def retrieve_memory(
    db: Session,
    *,
    query: str,
    tenant_id: str,
    project_id: str = "default",
    top_k: int = 6,
) -> MemoryContext:
    """Retrieve relevant knowledge. Returns citations with source_uri + hash."""
    result: HybridRetrievalResult = hybrid_search(
        db,
        query=query,
        tenant_id=tenant_id,
        project_id=project_id,
        top_k=top_k,
    )

    hits = [
        {
            "record_id": h.record_id,
            "title": h.title,
            "score": h.score,
            "text": h.text[:500],
            "source_uri": h.source_uri,
            "hash_sha256": h.hash_sha256,
        }
        for h in result.hits
    ]

    return MemoryContext(
        query=query,
        tenant_id=tenant_id,
        hits=hits,
        citations=result.citations,
        top_score=result.top_score,
    )
