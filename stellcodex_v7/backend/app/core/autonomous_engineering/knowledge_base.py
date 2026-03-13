"""Local deterministic manufacturing knowledge retrieval."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.knowledge.providers import build_embedding_provider, build_sparse_provider, build_vector_provider


_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "manufacturing_knowledge.json"


@dataclass(frozen=True)
class KnowledgeDocument:
    doc_id: str
    title: str
    text: str
    tags: tuple[str, ...]

    def to_reference(self, *, score: float) -> dict[str, Any]:
        return {
            "id": self.doc_id,
            "title": self.title,
            "tags": list(self.tags),
            "score": round(float(score), 6),
        }


class EngineeringKnowledgeBase:
    def __init__(self) -> None:
        self.embedding_provider = build_embedding_provider()
        self.vector_index_provider = build_vector_provider()
        self.sparse_search_provider = build_sparse_provider()
        self.documents = self._load_documents()
        self._index_documents()

    def _load_documents(self) -> dict[str, KnowledgeDocument]:
        payload = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
        documents: dict[str, KnowledgeDocument] = {}
        for row in payload:
            doc_id = str(row.get("id") or "").strip()
            if not doc_id:
                continue
            title = str(row.get("title") or doc_id)
            text = str(row.get("text") or "")
            tags = tuple(sorted({str(item).strip().lower() for item in row.get("tags") or [] if str(item).strip()}))
            documents[doc_id] = KnowledgeDocument(doc_id=doc_id, title=title, text=text, tags=tags)
        return documents

    def _index_documents(self) -> None:
        self.vector_index_provider.clear()
        self.sparse_search_provider.clear()
        texts = [document.text for document in self.documents.values()]
        vectors = self.embedding_provider.embed(texts)
        for index, document in enumerate(self.documents.values()):
            vector = vectors[index] if index < len(vectors) else []
            self.vector_index_provider.upsert(
                record_id=document.doc_id,
                vector=vector,
                metadata={"record_id": document.doc_id, "text": document.text},
            )
            self.sparse_search_provider.upsert(record_id=document.doc_id, text=document.text)

    def diagnostics(self) -> dict[str, Any]:
        return {
            "document_count": len(self.documents),
            "vector_provider": str(self.vector_index_provider.name),
            "sparse_provider": str(self.sparse_search_provider.name),
            "embedding_model": str(self.embedding_provider.model_name),
        }

    def retrieve(self, query: str, *, top_k: int = 4, tags: list[str] | None = None) -> list[dict[str, Any]]:
        if not self.documents:
            return []
        normalized_tags = {str(item).strip().lower() for item in tags or [] if str(item).strip()}
        allowed_ids = {
            doc_id
            for doc_id, document in self.documents.items()
            if not normalized_tags or normalized_tags.intersection(document.tags)
        }
        if not allowed_ids:
            allowed_ids = set(self.documents)
        query_vector = self.embedding_provider.embed([query or "manufacturing engineering review"])[0]
        dense_hits = self.vector_index_provider.search(
            query_vector=query_vector,
            top_k=max(4, int(top_k) * 2),
            allowed_ids=allowed_ids,
        )
        sparse_hits = self.sparse_search_provider.search(
            query=query or "manufacturing engineering review",
            top_k=max(4, int(top_k) * 2),
            allowed_ids=allowed_ids,
        )
        combined: dict[str, float] = {}
        for rank, (doc_id, score) in enumerate(dense_hits, start=1):
            combined[doc_id] = combined.get(doc_id, 0.0) + (0.65 * max(float(score), 0.0)) + (0.35 / (rank + 1))
        for rank, (doc_id, score) in enumerate(sparse_hits, start=1):
            combined[doc_id] = combined.get(doc_id, 0.0) + min(float(score), 12.0) / 12.0 + (0.25 / (rank + 1))
        ranked = sorted(combined.items(), key=lambda item: item[1], reverse=True)
        references: list[dict[str, Any]] = []
        for doc_id, score in ranked[: max(1, int(top_k))]:
            document = self.documents.get(doc_id)
            if document is None:
                continue
            references.append(document.to_reference(score=score))
        return references


@lru_cache(maxsize=1)
def load_default_knowledge_base() -> EngineeringKnowledgeBase:
    return EngineeringKnowledgeBase()
