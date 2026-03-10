from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.event_bus import EventBus, default_event_bus
from app.stellai.agents import (
    ExecutorAgent,
    MemoryManagerAgent,
    PlannerAgent,
    ResearcherAgent,
    RetrieverAgent,
    SelfEvaluatorAgent,
)
from app.stellai.events import RuntimeEventHub, phase2_event_sink
from app.stellai.knowledge import get_context_bundle
from app.stellai.memory import MemoryManager
from app.stellai.retrieval import RetrievalEngine
from app.stellai.tools import SafeToolExecutor
from app.stellai.types import RuntimeEvent, RuntimeRequest, RuntimeResponse


class StellAIRuntime:
    def __init__(
        self,
        *,
        planner: PlannerAgent | None = None,
        retriever: RetrieverAgent | None = None,
        researcher: ResearcherAgent | None = None,
        executor: ExecutorAgent | None = None,
        memory_agent: MemoryManagerAgent | None = None,
        evaluator: SelfEvaluatorAgent | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        retrieval_engine = RetrievalEngine()
        memory_manager = MemoryManager()
        self.planner = planner or PlannerAgent()
        self.retriever = retriever or RetrieverAgent(retrieval_engine)
        self.researcher = researcher or ResearcherAgent(retrieval_engine)
        self.executor = executor or ExecutorAgent(SafeToolExecutor(retrieval_engine=retrieval_engine))
        self.memory_agent = memory_agent or MemoryManagerAgent(memory_manager)
        self.evaluator = evaluator or SelfEvaluatorAgent()
        self.event_bus = event_bus or default_event_bus()

    def run(self, *, request: RuntimeRequest, db: Session | None = None) -> RuntimeResponse:
        hub = RuntimeEventHub(phase2_event_sink(self.event_bus, request.context))
        hub.emit(
            RuntimeEvent(
                event_type="started",
                agent="runtime",
                payload={
                    "session_id": request.context.session_id,
                    "trace_id": request.context.trace_id,
                    "tenant_id": request.context.tenant_id,
                    "project_id": request.context.project_id,
                },
            )
        )
        memory_before = self.memory_agent.load(context=request.context, query=request.message)
        hub.emit(
            RuntimeEvent(
                event_type="loaded",
                agent="memory",
                payload={"session_items": len(memory_before.session), "long_term_items": len(memory_before.long_term)},
            )
        )

        plan = self.planner.plan(request=request, memory=memory_before)
        hub.emit(RuntimeEvent(event_type="planned", agent="planner", payload=plan.task_graph.to_dict()))

        retrieval = self.retriever.retrieve(request=request, db=db)
        hub.emit(
            RuntimeEvent(
                event_type="retrieved",
                agent="retriever",
                payload={"chunk_count": len(retrieval.chunks), "top_score": retrieval.top_score},
            )
        )
        context_bundle: dict[str, Any] = {"relevant_records": [], "source_references": []}
        if db is not None:
            try:
                context_bundle = get_context_bundle(
                    db=db,
                    context=request.context,
                    query=request.message,
                    top_k=request.top_k,
                )
                hub.emit(
                    RuntimeEvent(
                        event_type="bundled",
                        agent="knowledge",
                        payload={
                            "record_count": len(context_bundle.get("relevant_records") or []),
                            "source_refs": context_bundle.get("source_references") or [],
                        },
                    )
                )
            except Exception as exc:
                hub.emit(
                    RuntimeEvent(
                        event_type="bundle_failed",
                        agent="knowledge",
                        payload={"error": str(exc)},
                    )
                )

        if plan.needs_research or retrieval.top_score < 0.2:
            researched = self.researcher.expand_and_retrieve(request=request, base=retrieval, db=db)
            if researched.top_score >= retrieval.top_score:
                retrieval = researched
            hub.emit(
                RuntimeEvent(
                    event_type="expanded",
                    agent="researcher",
                    payload={"chunk_count": len(retrieval.chunks), "top_score": retrieval.top_score},
                )
            )

        tool_results = self.executor.execute(context=request.context, db=db, calls=plan.tool_calls)
        hub.emit(
            RuntimeEvent(
                event_type="executed",
                agent="executor",
                payload={"calls": len(plan.tool_calls), "results": [item.to_dict() for item in tool_results]},
            )
        )

        reply = self._compose_reply(
            message=request.message,
            retrieval=retrieval,
            tool_results=tool_results,
            context_bundle=context_bundle,
        )
        evaluation = self.evaluator.evaluate(
            request=request,
            retrieval=retrieval,
            tool_results=tool_results,
            reply=reply,
            context_bundle=context_bundle,
            retried=False,
        )
        hub.emit(
            RuntimeEvent(
                event_type="evaluated",
                agent="self_eval",
                payload=evaluation.to_dict(),
            )
        )

        if evaluation.retry_recommended:
            retried_retrieval = self.researcher.expand_and_retrieve(request=request, base=retrieval, db=db)
            improved = (
                retried_retrieval.top_score > retrieval.top_score
                or len(retried_retrieval.chunks) > len(retrieval.chunks)
            )
            hub.emit(
                RuntimeEvent(
                    event_type="retry_considered",
                    agent="self_eval",
                    payload={
                        "improved": improved,
                        "previous_top_score": retrieval.top_score,
                        "retry_top_score": retried_retrieval.top_score,
                        "previous_chunk_count": len(retrieval.chunks),
                        "retry_chunk_count": len(retried_retrieval.chunks),
                    },
                )
            )
            if improved:
                retrieval = retried_retrieval
                reply = self._compose_reply(
                    message=request.message,
                    retrieval=retrieval,
                    tool_results=tool_results,
                    context_bundle=context_bundle,
                )
            evaluation = self.evaluator.evaluate(
                request=request,
                retrieval=retrieval,
                tool_results=tool_results,
                reply=reply,
                context_bundle=context_bundle,
                retried=True,
            )
            hub.emit(
                RuntimeEvent(
                    event_type="re_evaluated",
                    agent="self_eval",
                    payload=evaluation.to_dict(),
                )
            )

        memory_after = self.memory_agent.update(
            context=request.context,
            user_text=request.message,
            reply_text=reply,
            retrieval=retrieval,
            tool_results=tool_results,
            evaluation=evaluation.to_dict(),
        )
        hub.emit(
            RuntimeEvent(
                event_type="updated",
                agent="memory",
                payload={"session_items": len(memory_after.session), "long_term_items": len(memory_after.long_term)},
            )
        )
        hub.emit(
            RuntimeEvent(
                event_type="completed",
                agent="runtime",
                payload={"reply_length": len(reply), "tool_result_count": len(tool_results)},
            )
        )
        return RuntimeResponse(
            session_id=request.context.session_id,
            trace_id=request.context.trace_id,
            reply=reply,
            plan=plan.task_graph,
            retrieval=retrieval,
            tool_results=tool_results,
            memory=memory_after,
            evaluation=evaluation,
            events=hub.events,
        )

    def _compose_reply(self, *, message: str, retrieval, tool_results, context_bundle: dict[str, Any]) -> str:
        lines: list[str] = []
        if tool_results:
            lines.append("Tool results:")
            for item in tool_results:
                if item.status == "ok":
                    output = item.output if isinstance(item.output, dict) else {}
                    summary_bits: list[str] = []
                    if "status" in output:
                        summary_bits.append(f"status={output.get('status')}")
                    if "state" in output:
                        summary_bits.append(f"state={output.get('state')}")
                    if "approval_required" in output:
                        summary_bits.append(f"approval_required={output.get('approval_required')}")
                    if not summary_bits:
                        summary_bits.append("ok")
                    lines.append(f"- {item.tool_name}: {'; '.join(summary_bits)}")
                else:
                    lines.append(f"- {item.tool_name}: {item.status} ({item.reason})")

        if retrieval.chunks:
            lines.append("Grounded context:")
            for idx, chunk in enumerate(retrieval.chunks[:3], start=1):
                preview = " ".join(chunk.text.strip().split())[:220]
                lines.append(f"[{idx}] {chunk.source_ref} :: {preview}")
        else:
            lines.append("No grounded context was retrieved for this query.")
        bundle_refs = context_bundle.get("source_references") if isinstance(context_bundle, dict) else []
        if isinstance(bundle_refs, list) and bundle_refs:
            lines.append("Knowledge provenance:")
            for idx, source_ref in enumerate(bundle_refs[:3], start=1):
                lines.append(f"({idx}) {source_ref}")

        if not tool_results and not retrieval.chunks:
            lines.append("Try adding `file_ids` or broaden the query scope.")
        return "\n".join(lines)
