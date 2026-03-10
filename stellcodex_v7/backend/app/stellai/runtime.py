from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.core.identity.stell_identity import (
    GENERAL_FAILURE_TEXT,
    PLANNER_UNAVAILABLE_TEXT,
    TOOL_LAYER_UNAVAILABLE_TEXT,
)
from app.core.event_bus import EventBus, default_event_bus
from app.core.runtime.response_guard import guard_text_or_default, guard_user_payload
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
from app.stellai.types import (
    MemorySnapshot,
    RetrievalResult,
    RuntimeEvent,
    RuntimeRequest,
    RuntimeResponse,
    SelfEvaluation,
    TaskGraph,
)


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
        try:
            memory_before = self.memory_agent.load(context=request.context, query=request.message)
        except Exception:
            memory_before = MemorySnapshot()
        hub.emit(
            RuntimeEvent(
                event_type="loaded",
                agent="memory",
                payload={"session_items": len(memory_before.session), "long_term_items": len(memory_before.long_term)},
            )
        )

        try:
            plan = self.planner.plan(request=request, memory=memory_before)
        except Exception:
            hub.emit(
                RuntimeEvent(
                    event_type="planner_failed",
                    agent="planner",
                    payload={"reason": "planner_unavailable"},
                )
            )
            return self._safe_response(
                request=request,
                reply=PLANNER_UNAVAILABLE_TEXT,
                issue="planner_unavailable",
                events=hub.events,
                memory=memory_before,
            )
        hub.emit(RuntimeEvent(event_type="planned", agent="planner", payload=plan.task_graph.to_dict()))

        try:
            retrieval = self.retriever.retrieve(request=request, db=db)
        except Exception:
            retrieval = RetrievalResult(query=request.message, chunks=[], embedding_dim=0)
            hub.emit(
                RuntimeEvent(
                    event_type="retriever_failed",
                    agent="retriever",
                    payload={"reason": "retriever_unavailable"},
                )
            )
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
            except Exception:
                hub.emit(
                    RuntimeEvent(
                        event_type="bundle_failed",
                        agent="knowledge",
                        payload={"reason": "knowledge_bundle_failed"},
                    )
                )

        if plan.needs_research or retrieval.top_score < 0.2:
            try:
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
            except Exception:
                hub.emit(
                    RuntimeEvent(
                        event_type="researcher_failed",
                        agent="researcher",
                        payload={"reason": "research_expansion_failed"},
                    )
                )

        try:
            tool_results = self.executor.execute(context=request.context, db=db, calls=plan.tool_calls)
        except Exception:
            hub.emit(
                RuntimeEvent(
                    event_type="executor_failed",
                    agent="executor",
                    payload={"reason": "tool_layer_unavailable"},
                )
            )
            return self._safe_response(
                request=request,
                reply=TOOL_LAYER_UNAVAILABLE_TEXT,
                issue="tool_layer_unavailable",
                events=hub.events,
                memory=memory_before,
                plan=plan.task_graph,
                retrieval=retrieval,
            )
        hub.emit(
            RuntimeEvent(
                event_type="executed",
                agent="executor",
                payload={"calls": len(plan.tool_calls), "results": [item.to_dict() for item in tool_results]},
            )
        )

        try:
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
        except Exception:
            return self._safe_response(
                request=request,
                reply=GENERAL_FAILURE_TEXT,
                issue="reply_composition_failed",
                events=hub.events,
                memory=memory_before,
                plan=plan.task_graph,
                retrieval=retrieval,
                tool_results=tool_results,
            )
        hub.emit(
            RuntimeEvent(
                event_type="evaluated",
                agent="self_eval",
                payload=evaluation.to_dict(),
            )
        )

        if evaluation.retry_recommended:
            try:
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
            except Exception:
                hub.emit(
                    RuntimeEvent(
                        event_type="retry_skipped",
                        agent="self_eval",
                        payload={"reason": "retry_failed"},
                    )
                )

        try:
            memory_after = self.memory_agent.update(
                context=request.context,
                user_text=request.message,
                reply_text=reply,
                retrieval=retrieval,
                tool_results=tool_results,
                evaluation=evaluation.to_dict(),
            )
        except Exception:
            memory_after = memory_before
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
            reply=guard_text_or_default(reply, default=GENERAL_FAILURE_TEXT),
            plan=plan.task_graph,
            retrieval=retrieval,
            tool_results=tool_results,
            memory=memory_after,
            evaluation=evaluation,
            events=hub.events,
        )

    def _compose_reply(self, *, message: str, retrieval, tool_results, context_bundle: dict[str, Any]) -> str:
        successful_tools = [item for item in tool_results if item.status == "ok"]
        failed_tools = [item for item in tool_results if item.status != "ok"]
        if successful_tools:
            first_output = successful_tools[0].output if isinstance(successful_tools[0].output, dict) else {}
            if "recommended_process" in first_output:
                process = str(first_output.get("recommended_process") or "unknown")
                capability = str(first_output.get("capability_status") or "unknown")
                cost_estimate = first_output.get("cost_estimate") if isinstance(first_output.get("cost_estimate"), dict) else {}
                dfm_report = first_output.get("dfm_report") if isinstance(first_output.get("dfm_report"), dict) else {}
                estimated_unit_cost = cost_estimate.get("estimated_unit_cost", first_output.get("estimated_unit_cost"))
                currency = str(cost_estimate.get("currency") or "EUR")
                risk_count = int(dfm_report.get("risk_count") or len(dfm_report.get("risks") or []))
                reply = f"STELL-AI completed the engineering analysis. Recommended process: {process}. Capability: {capability}."
                if estimated_unit_cost is not None:
                    reply += f" Estimated unit cost: {estimated_unit_cost} {currency}."
                if risk_count:
                    reply += f" DFM risk count: {risk_count}."
                return guard_text_or_default(reply, default=GENERAL_FAILURE_TEXT)
            if "state" in first_output:
                return guard_text_or_default(
                    f"STELL-AI verified the decision state. State: {first_output.get('state')}.",
                    default=GENERAL_FAILURE_TEXT,
                )
            if "status" in first_output:
                return guard_text_or_default(
                    f"STELL-AI verified the file status. Status: {first_output.get('status')}.",
                    default=GENERAL_FAILURE_TEXT,
                )
            if "capability_status" in first_output:
                mode = str(first_output.get("mode") or "unknown")
                capability = str(first_output.get("capability_status") or "unknown")
                return guard_text_or_default(
                    f"STELL-AI verified the engineering capability. Mode: {mode}. Capability: {capability}.",
                    default=GENERAL_FAILURE_TEXT,
                )

        if failed_tools:
            return GENERAL_FAILURE_TEXT

        if retrieval.chunks:
            top_preview = " ".join(str(retrieval.chunks[0].text or "").split())[:180]
            if top_preview:
                return guard_text_or_default(
                    f"STELL-AI found grounded context. Summary: {top_preview}",
                    default=GENERAL_FAILURE_TEXT,
                )
            return "STELL-AI found grounded context."

        return "STELL-AI received the request. I can continue with a file_id for a more precise result."

    def _safe_response(
        self,
        *,
        request: RuntimeRequest,
        reply: str,
        issue: str,
        events: list[RuntimeEvent],
        memory: MemorySnapshot | None = None,
        plan: TaskGraph | None = None,
        retrieval: RetrievalResult | None = None,
        tool_results: list[Any] | None = None,
    ) -> RuntimeResponse:
        safe_plan = plan or TaskGraph.create([], metadata={"safe_failure": True, "reason": issue})
        safe_retrieval = retrieval or RetrievalResult(query=request.message, chunks=[], embedding_dim=0)
        safe_memory = memory or MemorySnapshot()
        safe_eval = SelfEvaluation(
            status="needs_attention",
            confidence=0.0,
            retry_recommended=False,
            revised=False,
            issues=[issue],
            actions=["fail_closed"],
        )
        return RuntimeResponse(
            session_id=request.context.session_id,
            trace_id=request.context.trace_id,
            reply=guard_text_or_default(reply, default=GENERAL_FAILURE_TEXT),
            plan=safe_plan,
            retrieval=safe_retrieval,
            tool_results=guard_user_payload(tool_results or []),
            memory=guard_user_payload(safe_memory),
            evaluation=safe_eval,
            events=events,
        )
