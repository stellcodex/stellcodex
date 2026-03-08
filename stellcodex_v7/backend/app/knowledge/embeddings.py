from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.knowledge.hash_utils import stable_hash_text
from app.knowledge.providers import EmbeddingProvider, build_embedding_provider
from app.knowledge.schemas import ChunkRecord


@dataclass(frozen=True)
class EmbeddedChunk:
    chunk: ChunkRecord
    vector: list[float]


class EmbeddingPipeline:
    def __init__(self, provider: EmbeddingProvider | None = None) -> None:
        self.provider = provider or build_embedding_provider()
        self._cache: dict[str, list[float]] = {}
        self.embedding_dim = int(self.provider.dim)

    def _cache_key(self, chunk: ChunkRecord) -> str:
        return stable_hash_text(f"{chunk.chunk_id}|{chunk.text}")

    def embed_chunks(self, chunks: list[ChunkRecord], *, batch_size: int = 32) -> list[EmbeddedChunk]:
        if not chunks:
            return []
        out: list[EmbeddedChunk] = []
        pending: list[ChunkRecord] = []
        pending_texts: list[str] = []
        for chunk in chunks:
            key = self._cache_key(chunk)
            cached = self._cache.get(key)
            if cached is not None:
                out.append(EmbeddedChunk(chunk=chunk, vector=cached))
                continue
            pending.append(chunk)
            pending_texts.append(chunk.text)

        for i in range(0, len(pending_texts), max(1, int(batch_size))):
            batch_chunks = pending[i : i + batch_size]
            batch_texts = pending_texts[i : i + batch_size]
            vectors = self.provider.embed(batch_texts)
            if len(vectors) != len(batch_chunks):
                raise RuntimeError("embedding provider returned inconsistent batch size")
            for chunk, vector in zip(batch_chunks, vectors):
                if len(vector) != self.embedding_dim:
                    raise RuntimeError("embedding dimension mismatch")
                key = self._cache_key(chunk)
                self._cache[key] = list(vector)
                out.append(EmbeddedChunk(chunk=chunk, vector=list(vector)))
        return out

    def cache_size(self) -> int:
        return len(self._cache)

    def provider_name(self) -> str:
        return str(self.provider.model_name)
