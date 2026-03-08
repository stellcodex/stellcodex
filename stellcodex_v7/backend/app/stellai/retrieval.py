from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from sqlalchemy.orm import Session

from app.knowledge.service import get_knowledge_service
from app.models.file import UploadFile
from app.stellai.types import RetrievalChunk, RetrievalResult, RuntimeContext

TOKEN_RE = re.compile(r"[a-z0-9_]+")
EMBEDDING_DIM = 128


def _tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall((text or "").lower())


def _embed(text: str, dim: int = EMBEDDING_DIM) -> list[float]:
    vector = [0.0] * dim
    for token in _tokenize(text):
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:2], "big") % dim
        sign = 1.0 if digest[2] % 2 == 0 else -1.0
        weight = 1.0 + (len(token) % 7) / 7.0
        vector[idx] += sign * weight
    norm = sum(value * value for value in vector) ** 0.5
    if norm <= 0:
        return vector
    return [value / norm for value in vector]


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    return sum(left * right for left, right in zip(a, b))


def _lexical_overlap(query: str, text: str) -> float:
    q_tokens = set(_tokenize(query))
    d_tokens = set(_tokenize(text))
    if not q_tokens or not d_tokens:
        return 0.0
    inter = len(q_tokens & d_tokens)
    return inter / max(1, len(q_tokens))


@dataclass
class SourceDocument:
    doc_id: str
    source_type: str
    source_ref: str
    text: str
    tenant_id: str | None = None
    project_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class RetrievalSource(Protocol):
    name: str

    def collect(
        self,
        *,
        query: str,
        context: RuntimeContext,
        db: Session | None,
        metadata_filters: dict[str, Any] | None,
    ) -> list[SourceDocument]:
        ...


class KnowledgeRecordSource:
    name = "knowledge_records"

    def collect(
        self,
        *,
        query: str,
        context: RuntimeContext,
        db: Session | None,
        metadata_filters: dict[str, Any] | None,
    ) -> list[SourceDocument]:
        if db is None:
            return []
        filters = metadata_filters if isinstance(metadata_filters, dict) else {}
        service = get_knowledge_service()
        top_k = int(filters.get("_top_k") or 8)
        source_types = filters.get("source_types") if isinstance(filters.get("source_types"), list) else None
        hits = service.search_knowledge(
            db=db,
            query=query,
            tenant_id=context.tenant_id,
            project_id=str(filters.get("project_id") or context.project_id),
            file_id=context.file_ids[0] if context.file_ids else None,
            top_k=max(1, min(top_k, 24)),
            source_types=source_types,
        )
        docs: list[SourceDocument] = []
        for item in hits:
            docs.append(
                SourceDocument(
                    doc_id=str(item.get("record_id") or ""),
                    source_type=str(item.get("source_type") or "knowledge"),
                    source_ref=str(item.get("source_ref") or ""),
                    text=str(item.get("text") or ""),
                    tenant_id=context.tenant_id,
                    project_id=str(item.get("metadata", {}).get("project_id") or context.project_id),
                    metadata=item.get("metadata") if isinstance(item.get("metadata"), dict) else {},
                )
            )
        return docs


class RepositorySource:
    name = "repository"

    def __init__(
        self,
        repo_root: str | Path = "/root/workspace",
        include_globs: tuple[str, ...] | None = None,
        max_files: int = 80,
        max_chars_per_file: int = 2400,
    ) -> None:
        self.repo_root = Path(repo_root)
        self.include_globs = include_globs or (
            "docs/**/*.md",
            "_truth/**/*.md",
            "PHASE2_*.md",
            "README.md",
        )
        self.max_files = max(1, int(max_files))
        self.max_chars_per_file = max(200, int(max_chars_per_file))

    def collect(
        self,
        *,
        query: str,
        context: RuntimeContext,
        db: Session | None,
        metadata_filters: dict[str, Any] | None,
    ) -> list[SourceDocument]:
        query_tokens = set(_tokenize(query))
        docs: list[SourceDocument] = []
        seen: set[Path] = set()
        for pattern in self.include_globs:
            for path in sorted(self.repo_root.glob(pattern)):
                if path in seen or not path.is_file():
                    continue
                seen.add(path)
                if len(docs) >= self.max_files:
                    return docs
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    continue
                if not text.strip():
                    continue
                lowered = text.lower()
                if query_tokens and not any(token in lowered for token in query_tokens):
                    continue
                rel = str(path.relative_to(self.repo_root))
                docs.append(
                    SourceDocument(
                        doc_id=f"repo:{rel}",
                        source_type="repository",
                        source_ref=rel,
                        text=text[: self.max_chars_per_file],
                        metadata={"path": rel},
                    )
                )
        return docs


class ArtifactSource:
    name = "artifacts"

    def __init__(self, memory_root: str | Path = "/root/workspace/_truth/records/memory", max_files: int = 120) -> None:
        self.memory_root = Path(memory_root)
        self.max_files = max(1, int(max_files))

    def collect(
        self,
        *,
        query: str,
        context: RuntimeContext,
        db: Session | None,
        metadata_filters: dict[str, Any] | None,
    ) -> list[SourceDocument]:
        if not self.memory_root.exists():
            return []
        query_tokens = set(_tokenize(query))
        docs: list[SourceDocument] = []
        for path in sorted(self.memory_root.glob("*.json")):
            if len(docs) >= self.max_files:
                break
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            text = str(payload.get("text") or "")
            if not text:
                continue
            lowered = text.lower()
            if query_tokens and not any(token in lowered for token in query_tokens):
                continue
            tenant_id = str(payload.get("tenant_id")) if payload.get("tenant_id") is not None else None
            project_id = str(payload.get("project_id")) if payload.get("project_id") is not None else None
            docs.append(
                SourceDocument(
                    doc_id=str(payload.get("record_id") or f"artifact:{path.name}"),
                    source_type="artifact",
                    source_ref=str(payload.get("source_uri") or path.name),
                    text=text[:2400],
                    tenant_id=tenant_id,
                    project_id=project_id,
                    metadata={
                        "title": str(payload.get("title") or ""),
                        "record_type": str(payload.get("record_type") or ""),
                        "path": str(path),
                    },
                )
            )
        return docs


class UploadSource:
    name = "uploads"

    def __init__(self, limit: int = 40) -> None:
        self.limit = max(1, int(limit))

    def collect(
        self,
        *,
        query: str,
        context: RuntimeContext,
        db: Session | None,
        metadata_filters: dict[str, Any] | None,
    ) -> list[SourceDocument]:
        if db is None:
            return []
        rows_query = db.query(UploadFile).filter(UploadFile.tenant_id == int(context.tenant_id))
        file_ids = list(context.file_ids)
        if file_ids:
            rows_query = rows_query.filter(UploadFile.file_id.in_(file_ids))
        rows = rows_query.order_by(UploadFile.updated_at.desc()).limit(self.limit).all()
        out: list[SourceDocument] = []
        for row in rows:
            meta = row.meta if isinstance(row.meta, dict) else {}
            decision = row.decision_json if isinstance(row.decision_json, dict) else {}
            summary_bits = [
                f"file_id={row.file_id}",
                f"name={row.original_filename}",
                f"status={row.status}",
                f"kind={meta.get('kind')}",
                f"mode={meta.get('mode')}",
            ]
            risks = decision.get("risk_flags") if isinstance(decision.get("risk_flags"), list) else []
            if risks:
                summary_bits.append(f"risks={','.join(str(item) for item in risks[:6])}")
            text = " | ".join(summary_bits)
            out.append(
                SourceDocument(
                    doc_id=f"upload:{row.file_id}",
                    source_type="upload",
                    source_ref=f"scx://files/{row.file_id}",
                    text=text,
                    tenant_id=str(row.tenant_id),
                    project_id=str(meta.get("project_id") or context.project_id),
                    metadata={
                        "file_id": row.file_id,
                        "status": str(row.status),
                        "kind": str(meta.get("kind") or ""),
                        "mode": str(meta.get("mode") or ""),
                    },
                )
            )
        return out


class RetrievalEngine:
    def __init__(self, sources: list[RetrievalSource] | None = None) -> None:
        self.sources = sources or [KnowledgeRecordSource(), RepositorySource(), ArtifactSource(), UploadSource()]

    def search(
        self,
        *,
        query: str,
        context: RuntimeContext,
        db: Session | None = None,
        top_k: int = 6,
        metadata_filters: dict[str, Any] | None = None,
    ) -> RetrievalResult:
        top_k = max(1, int(top_k))
        filters = metadata_filters if isinstance(metadata_filters, dict) else {}
        filters = {**filters, "_top_k": top_k}
        query_vec = _embed(query)
        filtered_out = 0
        scored: list[tuple[float, SourceDocument]] = []
        source_names: set[str] = set()
        for source in self.sources:
            docs = source.collect(query=query, context=context, db=db, metadata_filters=filters)
            source_names.add(source.name)
            for doc in docs:
                if doc.tenant_id is not None and doc.tenant_id != context.tenant_id:
                    filtered_out += 1
                    continue
                project_filter = str(filters.get("project_id") or "").strip()
                if project_filter and doc.project_id and doc.project_id != project_filter:
                    filtered_out += 1
                    continue
                dense = _cosine(query_vec, _embed(doc.text))
                sparse = _lexical_overlap(query, doc.text)
                score = (0.75 * dense) + (0.25 * sparse)
                if score <= 0:
                    continue
                scored.append((score, doc))

        scored.sort(key=lambda item: item[0], reverse=True)
        chunks: list[RetrievalChunk] = []
        for score, doc in scored[:top_k]:
            chunks.append(
                RetrievalChunk(
                    chunk_id=doc.doc_id,
                    source_type=doc.source_type,
                    source_ref=doc.source_ref,
                    text=doc.text,
                    score=score,
                    metadata=doc.metadata,
                )
            )
        return RetrievalResult(
            query=query,
            chunks=chunks,
            embedding_dim=EMBEDDING_DIM,
            filtered_out=filtered_out,
            used_sources=tuple(sorted(source_names)),
        )

    @staticmethod
    def assemble_grounding(chunks: list[RetrievalChunk], max_chars: int = 3200) -> str:
        total = 0
        lines: list[str] = []
        for idx, chunk in enumerate(chunks, start=1):
            snippet = " ".join(chunk.text.strip().split())
            block = f"[{idx}] {chunk.source_ref}: {snippet}"
            if total + len(block) > max_chars:
                break
            lines.append(block)
            total += len(block)
        return "\n".join(lines)
