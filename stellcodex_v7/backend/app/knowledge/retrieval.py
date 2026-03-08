from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.knowledge.embeddings import EmbeddingPipeline
from app.knowledge.schemas import ChunkRecord
from app.knowledge.vector_store import TenantAwareVectorStore


def _normalize_score(value: float, max_value: float) -> float:
    if max_value <= 0:
        return 0.0
    return max(0.0, min(1.0, float(value) / float(max_value)))


class HybridRetriever:
    def __init__(self, *, embeddings: EmbeddingPipeline, vector_store: TenantAwareVectorStore) -> None:
        self.embeddings = embeddings
        self.vector_store = vector_store

    def search(
        self,
        *,
        query: str,
        tenant_id: str,
        top_k: int,
        allowed_ids: set[str] | None = None,
        dedupe_by_record: bool = True,
    ) -> list[dict[str, Any]]:
        query_text = str(query or "").strip()
        if not query_text:
            return []
        probe_chunk = self.embeddings.embed_chunks(
            [
                ChunkRecord(
                    chunk_id="query_chunk",
                    record_id="query_record",
                    chunk_index=0,
                    text=query_text,
                    token_estimate=max(1, len(query_text.split())),
                    metadata={},
                )
            ],
            batch_size=1,
        )[0]
        hits = self.vector_store.search(
            tenant_id=tenant_id,
            query_vector=probe_chunk.vector,
            query_text=query_text,
            top_k=max(1, int(top_k)),
            allowed_ids=allowed_ids,
        )
        if not hits:
            return []

        max_dense = max(item.dense_score for item in hits) if hits else 1.0
        max_sparse = max(item.sparse_score for item in hits) if hits else 1.0

        scored: list[dict[str, Any]] = []
        for item in hits:
            dense = _normalize_score(item.dense_score, max_dense)
            sparse = _normalize_score(item.sparse_score, max_sparse)
            score = (0.65 * dense) + (0.35 * sparse)
            if score <= 0:
                continue
            metadata = item.metadata if isinstance(item.metadata, dict) else {}
            scored.append(
                {
                    "chunk_id": item.chunk_id,
                    "record_id": str(metadata.get("record_id") or ""),
                    "score": round(float(score), 6),
                    "dense_score": round(float(dense), 6),
                    "sparse_score": round(float(sparse), 6),
                    "metadata": metadata,
                }
            )
        scored.sort(key=lambda row: row["score"], reverse=True)

        if not dedupe_by_record:
            return scored[: max(1, int(top_k))]

        grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for row in scored:
            grouped[str(row.get("record_id") or row.get("chunk_id"))].append(row)
        reduced: list[dict[str, Any]] = []
        for _record_id, items in grouped.items():
            best = items[0]
            reduced.append(best)
        reduced.sort(key=lambda row: row["score"], reverse=True)
        return reduced[: max(1, int(top_k))]
