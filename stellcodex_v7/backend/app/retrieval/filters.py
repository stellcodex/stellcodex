from __future__ import annotations
from typing import Any
from app.retrieval.hybrid import RetrievalHit


def filter_by_score(hits: list[RetrievalHit], min_score: float = 0.1) -> list[RetrievalHit]:
    return [h for h in hits if h.score >= min_score]


def filter_by_source_type(hits: list[RetrievalHit], allowed: list[str]) -> list[RetrievalHit]:
    if not allowed:
        return hits
    allowed_set = set(allowed)
    return [h for h in hits if h.metadata.get("source_type") in allowed_set]


def deduplicate_by_record_id(hits: list[RetrievalHit]) -> list[RetrievalHit]:
    seen: set[str] = set()
    result: list[RetrievalHit] = []
    for h in hits:
        if h.record_id not in seen:
            seen.add(h.record_id)
            result.append(h)
    return result
