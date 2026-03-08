from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from typing import Any, Protocol


_TOKEN_RE = re.compile(r"[a-z0-9_]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall((text or "").lower())


def _dot(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0
    return float(sum(a * b for a, b in zip(left, right)))


class EmbeddingProvider(Protocol):
    model_name: str

    @property
    def dim(self) -> int:
        ...

    def embed(self, texts: list[str]) -> list[list[float]]:
        ...


class VectorIndexProvider(Protocol):
    name: str

    def clear(self) -> None:
        ...

    def upsert(self, *, record_id: str, vector: list[float], metadata: dict[str, Any] | None = None) -> None:
        ...

    def search(self, *, query_vector: list[float], top_k: int, allowed_ids: set[str] | None = None) -> list[tuple[str, float]]:
        ...


class SparseSearchProvider(Protocol):
    name: str

    def clear(self) -> None:
        ...

    def upsert(self, *, record_id: str, text: str) -> None:
        ...

    def search(self, *, query: str, top_k: int, allowed_ids: set[str] | None = None) -> list[tuple[str, float]]:
        ...


@dataclass
class HashEmbeddingProvider:
    model_name: str = "hash-embedding-v1"
    _dim: int = 256

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        out: list[list[float]] = []
        for raw in texts:
            vec = [0.0] * self._dim
            for token in _tokenize(raw):
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                idx = int.from_bytes(digest[:2], "big") % self._dim
                sign = 1.0 if digest[2] % 2 == 0 else -1.0
                vec[idx] += sign * (1.0 + (len(token) % 7) / 7.0)
            norm = math.sqrt(sum(value * value for value in vec))
            if norm > 0:
                vec = [value / norm for value in vec]
            out.append(vec)
        return out


class SentenceTransformerEmbeddingProvider:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        from sentence_transformers import SentenceTransformer  # type: ignore

        self.model_name = model_name
        # local_files_only keeps this deterministic in offline environments.
        self._model = SentenceTransformer(model_name, local_files_only=True)
        self._dim = int(self._model.get_sentence_embedding_dimension())

    @property
    def dim(self) -> int:
        return self._dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        vectors = self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return [list(map(float, row.tolist())) for row in vectors]


class InMemoryVectorIndexProvider:
    name = "in_memory_vector_index"

    def __init__(self) -> None:
        self._vectors: dict[str, list[float]] = {}

    def clear(self) -> None:
        self._vectors.clear()

    def upsert(self, *, record_id: str, vector: list[float], metadata: dict[str, Any] | None = None) -> None:
        _ = metadata
        self._vectors[str(record_id)] = list(vector)

    def search(self, *, query_vector: list[float], top_k: int, allowed_ids: set[str] | None = None) -> list[tuple[str, float]]:
        scored: list[tuple[str, float]] = []
        for record_id, vector in self._vectors.items():
            if allowed_ids is not None and record_id not in allowed_ids:
                continue
            score = _dot(query_vector, vector)
            if score <= 0:
                continue
            scored.append((record_id, score))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[: max(1, int(top_k))]


class ChromaVectorIndexProvider:
    name = "chroma"

    def __init__(self, *, collection_name: str = "stellcodex_knowledge") -> None:
        import chromadb  # type: ignore

        self._client = chromadb.Client()
        self._collection = self._client.get_or_create_collection(name=collection_name)

    def clear(self) -> None:
        self._collection.delete(where={})

    def upsert(self, *, record_id: str, vector: list[float], metadata: dict[str, Any] | None = None) -> None:
        meta = metadata if isinstance(metadata, dict) else {}
        self._collection.upsert(
            ids=[str(record_id)],
            embeddings=[list(vector)],
            metadatas=[meta],
            documents=[meta.get("text", "") if isinstance(meta.get("text"), str) else ""],
        )

    def search(self, *, query_vector: list[float], top_k: int, allowed_ids: set[str] | None = None) -> list[tuple[str, float]]:
        if allowed_ids is not None and not allowed_ids:
            return []
        result = self._collection.query(
            query_embeddings=[list(query_vector)],
            n_results=max(1, int(top_k)),
            where={"record_id": {"$in": sorted(allowed_ids)}} if allowed_ids else None,
        )
        ids = (result.get("ids") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        out: list[tuple[str, float]] = []
        for idx, record_id in enumerate(ids):
            distance = float(distances[idx]) if idx < len(distances) else 1.0
            # Chroma distance is lower-is-better; invert to score.
            score = max(0.0, 1.0 - distance)
            if score > 0:
                out.append((str(record_id), score))
        out.sort(key=lambda item: item[1], reverse=True)
        return out


class BM25SparseProvider:
    name = "bm25_fallback"

    def __init__(self) -> None:
        self._docs: dict[str, list[str]] = {}
        self._doc_lengths: dict[str, int] = {}
        self._df: dict[str, int] = {}
        self._avgdl: float = 0.0

    def clear(self) -> None:
        self._docs.clear()
        self._doc_lengths.clear()
        self._df.clear()
        self._avgdl = 0.0

    def upsert(self, *, record_id: str, text: str) -> None:
        rid = str(record_id)
        if rid in self._docs:
            self._remove_doc(rid)
        tokens = _tokenize(text)
        self._docs[rid] = tokens
        self._doc_lengths[rid] = len(tokens)
        for token in set(tokens):
            self._df[token] = self._df.get(token, 0) + 1
        self._avgdl = (
            (sum(self._doc_lengths.values()) / max(1, len(self._doc_lengths)))
            if self._doc_lengths
            else 0.0
        )

    def _remove_doc(self, record_id: str) -> None:
        tokens = self._docs.pop(record_id, [])
        self._doc_lengths.pop(record_id, None)
        for token in set(tokens):
            current = self._df.get(token, 0)
            if current <= 1:
                self._df.pop(token, None)
            else:
                self._df[token] = current - 1

    def search(self, *, query: str, top_k: int, allowed_ids: set[str] | None = None) -> list[tuple[str, float]]:
        q_tokens = _tokenize(query)
        if not q_tokens or not self._docs:
            return []
        k1 = 1.5
        b = 0.75
        n_docs = max(1, len(self._docs))
        scored: list[tuple[str, float]] = []
        for record_id, tokens in self._docs.items():
            if allowed_ids is not None and record_id not in allowed_ids:
                continue
            if not tokens:
                continue
            tf: dict[str, int] = {}
            for token in tokens:
                tf[token] = tf.get(token, 0) + 1
            doc_len = max(1, self._doc_lengths.get(record_id, len(tokens)))
            score = 0.0
            for token in q_tokens:
                freq = tf.get(token, 0)
                if freq <= 0:
                    continue
                df = self._df.get(token, 0)
                idf = math.log(1 + (n_docs - df + 0.5) / (df + 0.5))
                denom = freq + k1 * (1 - b + b * (doc_len / max(self._avgdl, 1e-6)))
                score += idf * ((freq * (k1 + 1)) / max(denom, 1e-9))
            if score > 0:
                scored.append((record_id, score))
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[: max(1, int(top_k))]


class RankBM25SparseProvider:
    name = "rank_bm25"

    def __init__(self) -> None:
        from rank_bm25 import BM25Okapi  # type: ignore

        self._bm25_cls = BM25Okapi
        self._ids: list[str] = []
        self._docs: list[list[str]] = []
        self._bm25: Any = None

    def clear(self) -> None:
        self._ids = []
        self._docs = []
        self._bm25 = None

    def upsert(self, *, record_id: str, text: str) -> None:
        rid = str(record_id)
        tokens = _tokenize(text)
        if rid in self._ids:
            idx = self._ids.index(rid)
            self._docs[idx] = tokens
        else:
            self._ids.append(rid)
            self._docs.append(tokens)
        self._bm25 = self._bm25_cls(self._docs) if self._docs else None

    def search(self, *, query: str, top_k: int, allowed_ids: set[str] | None = None) -> list[tuple[str, float]]:
        if self._bm25 is None:
            return []
        q_tokens = _tokenize(query)
        if not q_tokens:
            return []
        scores = self._bm25.get_scores(q_tokens)
        pairs: list[tuple[str, float]] = []
        for idx, score in enumerate(scores):
            rid = self._ids[idx]
            if allowed_ids is not None and rid not in allowed_ids:
                continue
            if float(score) <= 0:
                continue
            pairs.append((rid, float(score)))
        pairs.sort(key=lambda item: item[1], reverse=True)
        return pairs[: max(1, int(top_k))]


def build_embedding_provider() -> EmbeddingProvider:
    try:
        return SentenceTransformerEmbeddingProvider()
    except Exception:
        return HashEmbeddingProvider()


def build_vector_provider() -> VectorIndexProvider:
    try:
        return ChromaVectorIndexProvider()
    except Exception:
        return InMemoryVectorIndexProvider()


def build_sparse_provider() -> SparseSearchProvider:
    try:
        return RankBM25SparseProvider()
    except Exception:
        return BM25SparseProvider()
