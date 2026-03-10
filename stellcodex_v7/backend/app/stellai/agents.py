from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from app.core.runtime.response_guard import guard_user_payload
from app.stellai.memory import MemoryManager
from app.stellai.retrieval import RetrievalEngine
from app.stellai.tools import SafeToolExecutor, ToolCall
from app.stellai.types import (
    MemorySnapshot,
    PlanNode,
    RetrievalResult,
    RuntimeContext,
    RuntimeRequest,
    SelfEvaluation,
    TaskGraph,
    ToolExecution,
)


RESEARCH_HINTS = {
    "why",
    "how",
    "explain",
    "root cause",
    "compare",
    "analyze",
    "investigate",
    "research",
}


def _needs_research(message: str) -> bool:
    lowered = (message or "").lower()
    return any(token in lowered for token in RESEARCH_HINTS)


def _infer_tools(message: str, file_ids: tuple[str, ...]) -> list[ToolCall]:
    lowered = (message or "").lower()
    calls: list[ToolCall] = []
    seen: set[str] = set()

    def _append(name: str, params: dict[str, Any] | None = None) -> None:
        if name in seen:
            return
        seen.add(name)
        calls.append(ToolCall(name=name, params=params or {}))

    if ("status" in lowered or "state" in lowered) and file_ids:
        _append("upload.status", {"file_id": file_ids[0]})
    if ("decision" in lowered or "dfm" in lowered or "risk" in lowered) and file_ids:
        _append("upload.decision", {"file_id": file_ids[0]})
    if ("recompute" in lowered or "rerun" in lowered or "reanalyze" in lowered) and file_ids:
        _append("orchestrator.recompute", {"file_id": file_ids[0]})
    if ("capability" in lowered or "support" in lowered or "format" in lowered) and file_ids:
        _append("cad_load", {"file_id": file_ids[0]})
    if ("mesh" in lowered or "geometry" in lowered or "analysis" in lowered or "analiz" in lowered) and file_ids:
        _append("mesh_analyze", {"file_id": file_ids[0]})
    if ("volume" in lowered or "hacim" in lowered) and file_ids:
        _append("volume_compute", {"file_id": file_ids[0]})
    if ("surface" in lowered or "yuzey" in lowered or "yüzey" in lowered) and file_ids:
        _append("surface_area_compute", {"file_id": file_ids[0]})
    if ("feature" in lowered or "özellik" in lowered or "ozellik" in lowered) and file_ids:
        _append("feature_extract", {"file_id": file_ids[0]})
    if (
        "dfm" in lowered
        or "manufactur" in lowered
        or "risk" in lowered
        or "precheck" in lowered
        or "cost" in lowered
        or "price" in lowered
        or "quote" in lowered
        or "maliyet" in lowered
        or "fiyat" in lowered
        or "plan" in lowered
        or "workflow" in lowered
        or "rapor" in lowered
        or ("report" in lowered and file_ids)
    ) and file_ids:
        _append("dfm_precheck", {"file_id": file_ids[0]})
    if "system info" in lowered:
        _append("system_info")
    if "runtime status" in lowered:
        _append("runtime_status")
    if "process status" in lowered:
        _append("process_status")
    if "disk usage" in lowered:
        _append("disk_usage")
    if "list directory" in lowered:
        _append("list_directory", {"path": "."})
    if "search files" in lowered:
        _append("search_files", {"path": ".", "pattern": "status"})
    if "doc search" in lowered:
        _append("doc_search", {"query": message})
    if "knowledge lookup" in lowered:
        _append("knowledge_lookup", {"query": message})
    if "summary" in lowered and "text" in lowered:
        _append("text_summary", {"query": message})
    return calls


@dataclass
class PlannerOutput:
    task_graph: TaskGraph
    tool_calls: list[ToolCall]
    needs_research: bool


class PlannerAgent:
    def plan(self, *, request: RuntimeRequest, memory: MemorySnapshot) -> PlannerOutput:
        explicit_calls: list[ToolCall] = []
        for raw in request.tool_requests:
            if not isinstance(raw, dict):
                continue
            name = str(raw.get("name") or "").strip()
            if not name:
                continue
            params = raw.get("params") if isinstance(raw.get("params"), dict) else {}
            explicit_calls.append(ToolCall(name=name, params=params))
        inferred_calls = _infer_tools(request.message, request.context.file_ids)
        tool_calls = explicit_calls if explicit_calls else inferred_calls
        needs_research = _needs_research(request.message)

        nodes: list[PlanNode] = [
            PlanNode(
                node_id=f"n_{uuid4().hex[:8]}",
                kind="retrieve",
                description="retrieve relevant context",
                payload={"top_k": request.top_k},
            ),
        ]
        if needs_research:
            nodes.append(
                PlanNode(
                    node_id=f"n_{uuid4().hex[:8]}",
                    kind="research",
                    description="expand context if retrieval signal is weak",
                    depends_on=(nodes[-1].node_id,),
                )
            )
        if tool_calls:
            nodes.append(
                PlanNode(
                    node_id=f"n_{uuid4().hex[:8]}",
                    kind="execute_tools",
                    description="run allowlisted tools with permission checks",
                    depends_on=(nodes[-1].node_id,),
                    payload={"tools": [call.name for call in tool_calls]},
                )
            )
        nodes.append(
            PlanNode(
                node_id=f"n_{uuid4().hex[:8]}",
                kind="memory_update",
                description="persist session and long-term memory",
                depends_on=(nodes[-1].node_id,),
            )
        )
        graph = TaskGraph.create(
            nodes,
            metadata={
                "needs_research": needs_research,
                "tool_count": len(tool_calls),
                "session_memory_items": len(memory.session),
            },
        )
        return PlannerOutput(task_graph=graph, tool_calls=tool_calls, needs_research=needs_research)


class RetrieverAgent:
    def __init__(self, engine: RetrievalEngine) -> None:
        self.engine = engine

    def retrieve(self, *, request: RuntimeRequest, db: Session | None) -> RetrievalResult:
        return self.engine.search(
            query=request.message,
            context=request.context,
            db=db,
            top_k=request.top_k,
            metadata_filters=request.metadata_filters,
        )


class ResearcherAgent:
    def __init__(self, engine: RetrievalEngine) -> None:
        self.engine = engine

    def expand_and_retrieve(
        self,
        *,
        request: RuntimeRequest,
        base: RetrievalResult,
        db: Session | None,
    ) -> RetrievalResult:
        chunk_terms: list[str] = []
        for chunk in base.chunks[:3]:
            ref = str(chunk.metadata.get("record_type") or chunk.source_type)
            if ref:
                chunk_terms.append(ref)
        expanded = " ".join([request.message] + chunk_terms).strip()
        if not expanded:
            expanded = request.message
        return self.engine.search(
            query=expanded,
            context=request.context,
            db=db,
            top_k=max(request.top_k, 8),
            metadata_filters=request.metadata_filters,
        )


class ExecutorAgent:
    def __init__(self, tool_executor: SafeToolExecutor) -> None:
        self.tool_executor = tool_executor

    def execute(self, *, context: RuntimeContext, db: Session | None, calls: list[ToolCall]) -> list[ToolExecution]:
        if not calls:
            return []
        return self.tool_executor.execute_calls(context=context, db=db, calls=calls)


class MemoryManagerAgent:
    def __init__(self, manager: MemoryManager) -> None:
        self.manager = manager

    def load(self, *, context: RuntimeContext, query: str) -> MemorySnapshot:
        return self.manager.load(context=context, query=query)

    def update(
        self,
        *,
        context: RuntimeContext,
        user_text: str,
        reply_text: str,
        retrieval: RetrievalResult,
        tool_results: list[ToolExecution],
        evaluation: dict[str, Any] | None = None,
    ) -> MemorySnapshot:
        self.manager.append_user_turn(context=context, text=user_text)
        memory_path = self.manager.append_stell_turn(
            context=context,
            text=reply_text,
            metadata={
                "retrieval_chunks": len(retrieval.chunks),
                "top_score": retrieval.top_score,
                "tool_results": guard_user_payload([item.to_dict() for item in tool_results]),
                "evaluation": guard_user_payload(evaluation or {}),
            },
        )
        snapshot = self.manager.load(context=context, query=user_text)
        if snapshot.long_term and memory_path is not None:
            snapshot.long_term[0]["memory_path"] = str(memory_path)
        return snapshot


class SelfEvaluatorAgent:
    def evaluate(
        self,
        *,
        request: RuntimeRequest,
        retrieval: RetrievalResult,
        tool_results: list[ToolExecution],
        reply: str,
        context_bundle: dict[str, Any],
        retried: bool = False,
    ) -> SelfEvaluation:
        issues: list[str] = []
        actions: list[str] = []

        successful_tools = [item for item in tool_results if item.status == "ok"]
        failed_tools = [item for item in tool_results if item.status != "ok"]
        if not retrieval.chunks and not successful_tools:
            issues.append("no_grounded_evidence")
            actions.append("expand retrieval scope or provide file_ids")

        if retrieval.chunks and retrieval.top_score < 0.18:
            issues.append("weak_grounding_signal")
            actions.append("retry retrieval with expanded query")

        if failed_tools:
            issues.append("tool_failures_present")
            actions.append("preserve fail-closed behavior")

        confidence = 0.25
        if retrieval.chunks:
            confidence += min(max(retrieval.top_score, 0.0), 0.45)
        if successful_tools:
            confidence += min(0.2, 0.07 * len(successful_tools))
        if not failed_tools:
            confidence += 0.1
        confidence = max(0.0, min(confidence, 0.95))

        retry_recommended = (
            not retried
            and (
                "no_grounded_evidence" in issues
                or "weak_grounding_signal" in issues
            )
        )

        if not issues:
            status = "pass"
            actions.append("no_changes_required")
        elif retried and confidence >= 0.45 and "no_grounded_evidence" not in issues:
            status = "revised"
            actions.append("retry_improved_answer")
        else:
            status = "needs_attention"
            if retried:
                actions.append("retry_completed_but_limit_reached")

        return SelfEvaluation(
            status=status,
            confidence=confidence,
            retry_recommended=retry_recommended,
            revised=retried and status == "revised",
            issues=issues,
            actions=actions,
        )
