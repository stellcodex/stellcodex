from __future__ import annotations

import re
from typing import Any

from app.stellai.retrieval import ArtifactSource, KnowledgeRecordSource, RepositorySource, RetrievalEngine, UploadSource
from app.stellai.tools_registry import ToolDefinition
from app.stellai.types import RuntimeContext, ToolExecution


def build_research_tools(*, retrieval_engine: RetrievalEngine | None) -> list[ToolDefinition]:
    shared_engine = retrieval_engine or RetrievalEngine()
    repo_engine = RetrievalEngine(sources=[RepositorySource()])
    knowledge_engine = RetrievalEngine(sources=[KnowledgeRecordSource(), ArtifactSource(), UploadSource()])

    return [
        ToolDefinition(
            name="doc_search",
            description="Search grounded retrieval sources with tenant and project filtering.",
            input_schema={"type": "object", "properties": {"query": {"type": "string"}, "top_k": {"type": "integer"}}},
            output_schema={"type": "object"},
            permission_scope="stellai.research.read",
            tenant_required=True,
            handler=_build_doc_search_handler(shared_engine),
            category="research",
            tags=("retrieval", "grounded"),
        ),
        ToolDefinition(
            name="repo_search",
            description="Search repository-backed knowledge only.",
            input_schema={"type": "object", "properties": {"query": {"type": "string"}, "top_k": {"type": "integer"}}},
            output_schema={"type": "object"},
            permission_scope="stellai.research.read",
            tenant_required=True,
            handler=_build_doc_search_handler(repo_engine, tool_name="repo_search"),
            category="research",
            tags=("retrieval", "repository"),
        ),
        ToolDefinition(
            name="knowledge_lookup",
            description="Search tenant-scoped artifact/upload knowledge sources.",
            input_schema={"type": "object", "properties": {"query": {"type": "string"}, "top_k": {"type": "integer"}}},
            output_schema={"type": "object"},
            permission_scope="stellai.research.read",
            tenant_required=True,
            handler=_build_doc_search_handler(knowledge_engine, tool_name="knowledge_lookup"),
            category="research",
            tags=("retrieval", "artifact"),
        ),
        ToolDefinition(
            name="text_summary",
            description="Produce concise summaries from provided text or retrieval-backed query results.",
            input_schema={"type": "object", "properties": {"text": {"type": "string"}, "query": {"type": "string"}}},
            output_schema={"type": "object"},
            permission_scope="stellai.research.read",
            tenant_required=True,
            handler=_build_text_summary_handler(shared_engine),
            category="research",
            tags=("summary", "grounded"),
        ),
    ]


def _build_doc_search_handler(engine: RetrievalEngine, tool_name: str = "doc_search"):
    def _handler(context: RuntimeContext, db, params: dict[str, Any]) -> ToolExecution:
        query = str(params.get("query") or params.get("text") or "").strip()
        if not query:
            return ToolExecution(
                tool_name=tool_name,
                status="denied",
                reason="missing_query",
                output={"error": {"reason": "missing_query"}},
            )
        top_k = _bounded_int(params.get("top_k"), default=6, minimum=1, maximum=20)
        metadata_filters = {"project_id": context.project_id}
        if isinstance(params.get("metadata_filters"), dict):
            metadata_filters.update(params.get("metadata_filters"))
        result = engine.search(
            query=query,
            context=context,
            db=db,
            top_k=top_k,
            metadata_filters=metadata_filters,
        )
        allowed_sources = _normalized_source_filter(params.get("source_types"))
        chunks = list(result.chunks)
        if allowed_sources:
            chunks = [item for item in chunks if item.source_type in allowed_sources]
        results = [
            {
                "source_ref": item.source_ref,
                "source_type": item.source_type,
                "score": round(float(item.score), 6),
                "snippet": _compact(item.text, 320),
                "metadata": item.metadata,
            }
            for item in chunks
        ]
        citations = [item["source_ref"] for item in results]
        return ToolExecution(
            tool_name=tool_name,
            status="ok",
            output={
                "query": query,
                "result_count": len(results),
                "filtered_out": result.filtered_out,
                "used_sources": list(result.used_sources),
                "results": results,
                "citations": citations,
            },
        )

    return _handler


def _build_text_summary_handler(engine: RetrievalEngine):
    def _handler(context: RuntimeContext, db, params: dict[str, Any]) -> ToolExecution:
        explicit_text = str(params.get("text") or "").strip()
        query = str(params.get("query") or "").strip()
        citations: list[str] = []

        if explicit_text:
            source_text = explicit_text
        else:
            if not query:
                return ToolExecution(
                    tool_name="text_summary",
                    status="denied",
                    reason="missing_text_or_query",
                    output={"error": {"reason": "missing_text_or_query"}},
                )
            retrieval = engine.search(
                query=query,
                context=context,
                db=db,
                top_k=_bounded_int(params.get("top_k"), default=5, minimum=1, maximum=12),
                metadata_filters={"project_id": context.project_id},
            )
            citations = [chunk.source_ref for chunk in retrieval.chunks]
            source_text = "\n".join(chunk.text for chunk in retrieval.chunks)

        summary = _summarize_text(source_text, max_sentences=_bounded_int(params.get("max_sentences"), default=4, minimum=1, maximum=8))
        return ToolExecution(
            tool_name="text_summary",
            status="ok",
            output={"summary": summary, "citations": citations},
        )

    return _handler


def _summarize_text(text: str, *, max_sentences: int) -> str:
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    if not cleaned:
        return ""
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    compact = [segment.strip() for segment in sentences if segment.strip()]
    if not compact:
        return cleaned[:500]
    return " ".join(compact[:max_sentences])[:1200]


def _normalized_source_filter(value: Any) -> set[str]:
    if not isinstance(value, list):
        return set()
    out: set[str] = set()
    for item in value:
        text = str(item or "").strip().lower()
        if text:
            out.add(text)
    return out


def _compact(text: str, max_len: int) -> str:
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    return cleaned[:max_len]


def _bounded_int(value: Any, *, default: int, minimum: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except Exception:
        parsed = default
    return max(minimum, min(parsed, maximum))
