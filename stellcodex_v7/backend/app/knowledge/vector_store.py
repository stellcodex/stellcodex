from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.knowledge.embeddings import EmbeddedChunk
from app.knowledge.providers import (
    SparseSearchProvider,
    VectorIndexProvider,
    build_sparse_provider,
    build_vector_provider,
)


@dataclass(frozen=True)
class VectorHit:
    chunk_id: str
    dense_score: float
    sparse_score: float
    metadata: dict[str, Any]


class QdrantVectorStoreStub:
    name = "qdrant_stub"

    def upsert(self, *args, **kwargs):
        raise NotImplementedError("Qdrant adapter stub not implemented in this phase")

    def search(self, *args, **kwargs):
        raise NotImplementedError("Qdrant adapter stub not implemented in this phase")


class TenantAwareVectorStore:
    def __init__(
        self,
        *,
        vector_provider: VectorIndexProvider | None = None,
        sparse_provider: SparseSearchProvider | None = None,
    ) -> None:
        self.vector_provider = vector_provider or build_vector_provider()
        self.sparse_provider = sparse_provider or build_sparse_provider()
        self._metadata: dict[str, dict[str, Any]] = {}
        self._tombstones: set[str] = set()

    @staticmethod
    def namespaced_chunk_id(tenant_id: str, chunk_id: str) -> str:
        return f"tenant:{tenant_id}:{chunk_id}"

    def upsert_chunks(
        self,
        *,
        tenant_id: str,
        embedded_chunks: list[EmbeddedChunk],
        base_metadata: dict[str, Any],
        replace_existing: bool = True,
    ) -> list[str]:
        inserted_ids: list[str] = []
        for item in embedded_chunks:
            ns_id = self.namespaced_chunk_id(str(tenant_id), item.chunk.chunk_id)
            if replace_existing and ns_id in self._tombstones:
                self._tombstones.discard(ns_id)
            metadata = {
                **(base_metadata if isinstance(base_metadata, dict) else {}),
                **(item.chunk.metadata if isinstance(item.chunk.metadata, dict) else {}),
                "tenant_id": str(tenant_id),
                "record_id": item.chunk.record_id,
                "chunk_id": item.chunk.chunk_id,
                "chunk_index": int(item.chunk.chunk_index),
                "token_estimate": int(item.chunk.token_estimate),
            }
            self.vector_provider.upsert(record_id=ns_id, vector=item.vector, metadata=metadata)
            self.sparse_provider.upsert(record_id=ns_id, text=item.chunk.text)
            self._metadata[ns_id] = metadata
            inserted_ids.append(ns_id)
        return inserted_ids

    def mark_tombstone(self, namespaced_ids: list[str]) -> None:
        for item in namespaced_ids:
            self._tombstones.add(str(item))

    def search(
        self,
        *,
        tenant_id: str,
        query_vector: list[float],
        query_text: str,
        top_k: int,
        allowed_ids: set[str] | None = None,
    ) -> list[VectorHit]:
        prefix = f"tenant:{tenant_id}:"
        scoped_ids: set[str] = {item for item in self._metadata.keys() if item.startswith(prefix) and item not in self._tombstones}
        if allowed_ids is not None:
            scoped_ids = scoped_ids & set(allowed_ids)
        if not scoped_ids:
            return []

        dense = dict(self.vector_provider.search(query_vector=query_vector, top_k=max(top_k * 4, 32), allowed_ids=scoped_ids))
        sparse = dict(self.sparse_provider.search(query=query_text, top_k=max(top_k * 4, 32), allowed_ids=scoped_ids))

        hits: list[VectorHit] = []
        for ns_id in scoped_ids:
            hits.append(
                VectorHit(
                    chunk_id=ns_id,
                    dense_score=float(dense.get(ns_id, 0.0)),
                    sparse_score=float(sparse.get(ns_id, 0.0)),
                    metadata=self._metadata.get(ns_id, {}),
                )
            )
        return hits

    def metadata_for(self, namespaced_id: str) -> dict[str, Any]:
        return self._metadata.get(namespaced_id, {}).copy()

    def stats(self) -> dict[str, Any]:
        return {
            "vector_provider": getattr(self.vector_provider, "name", "unknown"),
            "sparse_provider": getattr(self.sparse_provider, "name", "unknown"),
            "stored_chunks": len(self._metadata),
            "tombstones": len(self._tombstones),
        }
