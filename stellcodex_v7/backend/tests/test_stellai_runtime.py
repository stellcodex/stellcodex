from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tempfile
import unittest

from app.stellai.agents import ExecutorAgent, MemoryManagerAgent, PlannerAgent, ResearcherAgent, RetrieverAgent, SelfEvaluatorAgent
from app.stellai.memory import LongTermMemoryStore, MemoryManager, SessionMemoryStore, WorkingMemoryStore
from app.stellai.retrieval import RetrievalEngine, SourceDocument
from app.stellai.runtime import StellAIRuntime
from app.stellai.tools import SafeToolExecutor, ToolCall
from app.stellai.types import MemorySnapshot, RetrievalResult, RuntimeContext, RuntimeRequest, ToolExecution


class _InMemorySource:
    name = "memory-source"

    def __init__(self, docs: list[SourceDocument]) -> None:
        self.docs = docs

    def collect(self, *, query, context, db, metadata_filters):
        return list(self.docs)


class _FakeRow:
    def __init__(self, *, file_id: str, tenant_id: int, status: str = "ready") -> None:
        self.file_id = file_id
        self.tenant_id = tenant_id
        self.status = status
        self.original_filename = "part.step"
        self.updated_at = None
        self.decision_json = {"state": "S5", "approval_required": True, "risk_flags": ["thin_wall"]}


class _FakeEventBus:
    def __init__(self) -> None:
        self.events: list[dict] = []

    def publish_event(self, **kwargs):
        self.events.append(kwargs)
        return {"id": f"evt-{len(self.events)}"}


class StellAIRuntimeTests(unittest.TestCase):
    def test_planner_flow_builds_task_graph(self) -> None:
        context = RuntimeContext(
            tenant_id="1",
            project_id="p1",
            principal_type="guest",
            principal_id="guest-1",
            session_id="s1",
            trace_id="t1",
            file_ids=("scx_11111111-1111-1111-1111-111111111111",),
            allowed_tools=frozenset({"upload.status"}),
        )
        planner = PlannerAgent()
        request = RuntimeRequest(message="show status for this file", context=context, top_k=4)
        out = planner.plan(request=request, memory=MemorySnapshot())
        self.assertEqual(out.task_graph.nodes[0].kind, "retrieve")
        self.assertTrue(any(node.kind == "execute_tools" for node in out.task_graph.nodes))
        self.assertEqual(out.tool_calls[0].name, "upload.status")

    def test_planner_routes_cost_and_plan_requests_to_engineering_precheck(self) -> None:
        context = RuntimeContext(
            tenant_id="1",
            project_id="p1",
            principal_type="guest",
            principal_id="guest-1",
            session_id="s1",
            trace_id="t1",
            file_ids=("scx_11111111-1111-1111-1111-111111111111",),
            allowed_tools=frozenset({"dfm_precheck"}),
        )
        planner = PlannerAgent()
        request = RuntimeRequest(message="bu parcanin maliyetini ve uretim planini analiz et", context=context, top_k=4)

        out = planner.plan(request=request, memory=MemorySnapshot())

        self.assertTrue(any(call.name == "dfm_precheck" for call in out.tool_calls))

    def test_retrieval_flow_applies_tenant_and_project_filters(self) -> None:
        docs = [
            SourceDocument(
                doc_id="d1",
                source_type="artifact",
                source_ref="a1",
                text="status ready file",
                tenant_id="1",
                project_id="p1",
            ),
            SourceDocument(
                doc_id="d2",
                source_type="artifact",
                source_ref="a2",
                text="status ready file",
                tenant_id="2",
                project_id="p1",
            ),
            SourceDocument(
                doc_id="d3",
                source_type="artifact",
                source_ref="a3",
                text="status ready file",
                tenant_id="1",
                project_id="p2",
            ),
        ]
        engine = RetrievalEngine(sources=[_InMemorySource(docs)])
        context = RuntimeContext(
            tenant_id="1",
            project_id="p1",
            principal_type="guest",
            principal_id="guest-1",
            session_id="s1",
            trace_id="t1",
            allowed_tools=frozenset(),
        )
        result = engine.search(query="ready status", context=context, top_k=5, metadata_filters={"project_id": "p1"})
        refs = [chunk.source_ref for chunk in result.chunks]
        self.assertEqual(refs, ["a1"])
        self.assertGreaterEqual(result.filtered_out, 2)

    def test_memory_update_flow_persists_long_term(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = MemoryManager(
                session_store=SessionMemoryStore(),
                working_store=WorkingMemoryStore(),
                long_term_store=LongTermMemoryStore(tmp_dir),
            )
            agent = MemoryManagerAgent(manager)
            context = RuntimeContext(
                tenant_id="1",
                project_id="p1",
                principal_type="guest",
                principal_id="guest-1",
                session_id="s1",
                trace_id="t1",
                allowed_tools=frozenset(),
            )
            retrieval = RetrievalResult(query="status", chunks=[], embedding_dim=128)
            snapshot = agent.update(
                context=context,
                user_text="status check",
                reply_text="status is ready",
                retrieval=retrieval,
                tool_results=[],
            )
            self.assertEqual(len(snapshot.session), 2)
            path = Path(tmp_dir) / "tenant_1" / "p1.jsonl"
            self.assertTrue(path.exists())
            self.assertIn("status is ready", path.read_text(encoding="utf-8"))

    def test_tenant_isolation_in_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            manager = MemoryManager(long_term_store=LongTermMemoryStore(tmp_dir))
            c1 = RuntimeContext(
                tenant_id="1",
                project_id="p1",
                principal_type="guest",
                principal_id="g1",
                session_id="s1",
                trace_id="t1",
                allowed_tools=frozenset(),
            )
            c2 = RuntimeContext(
                tenant_id="2",
                project_id="p1",
                principal_type="guest",
                principal_id="g2",
                session_id="s2",
                trace_id="t2",
                allowed_tools=frozenset(),
            )
            manager.append_stell_turn(context=c1, text="tenant one data")
            manager.append_stell_turn(context=c2, text="tenant two data")
            s1 = manager.load(context=c1, query="tenant data")
            s2 = manager.load(context=c2, query="tenant data")
            self.assertTrue(all(str(item.get("tenant_id")) == "1" for item in s1.long_term))
            self.assertTrue(all(str(item.get("tenant_id")) == "2" for item in s2.long_term))

    def test_permission_enforcement_and_safe_executor_behavior(self) -> None:
        executor = SafeToolExecutor(allowlist=frozenset({"runtime.echo", "upload.status"}))
        context = RuntimeContext(
            tenant_id="1",
            project_id="p1",
            principal_type="guest",
            principal_id="g1",
            session_id="s1",
            trace_id="t1",
            file_ids=("scx_11111111-1111-1111-1111-111111111111",),
            allowed_tools=frozenset({"runtime.echo"}),
        )
        out = executor.execute_calls(
            context=context,
            db=None,
            calls=[
                ToolCall(name="runtime.echo", params={"message": "hi"}),
                ToolCall(name="upload.status", params={}),
                ToolCall(name="unknown.tool", params={}),
            ],
        )
        self.assertEqual(out[0].status, "ok")
        self.assertEqual(out[1].status, "denied")
        self.assertEqual(out[1].reason, "tool_not_permitted_for_request")
        self.assertEqual(out[2].reason, "tool_not_allowlisted")

    def test_safe_executor_denies_cross_tenant_file_access(self) -> None:
        executor = SafeToolExecutor(allowlist=frozenset({"upload.status"}))
        context = RuntimeContext(
            tenant_id="1",
            project_id="p1",
            principal_type="guest",
            principal_id="g1",
            session_id="s1",
            trace_id="t1",
            file_ids=("scx_11111111-1111-1111-1111-111111111111",),
            allowed_tools=frozenset({"upload.status"}),
        )
        executor._load_upload = lambda _db, _file_id: _FakeRow(file_id="x", tenant_id=2)  # type: ignore[assignment]
        out = executor.execute_calls(context=context, db=None, calls=[ToolCall(name="upload.status", params={})])
        self.assertEqual(out[0].status, "denied")
        self.assertEqual(out[0].reason, "tenant_mismatch")

    def test_runtime_end_to_end(self) -> None:
        docs = [
            SourceDocument(
                doc_id="doc1",
                source_type="repository",
                source_ref="docs/one.md",
                text="workflow status and orchestrator state",
                tenant_id=None,
                project_id=None,
            )
        ]
        retrieval_engine = RetrievalEngine(sources=[_InMemorySource(docs)])
        memory_manager = MemoryManager(long_term_store=LongTermMemoryStore(tempfile.mkdtemp()))
        runtime = StellAIRuntime(
            planner=PlannerAgent(),
            retriever=RetrieverAgent(retrieval_engine),
            researcher=ResearcherAgent(retrieval_engine),
            executor=ExecutorAgent(SafeToolExecutor(allowlist=frozenset({"runtime.echo"}))),
            memory_agent=MemoryManagerAgent(memory_manager),
        )
        context = RuntimeContext(
            tenant_id="1",
            project_id="p1",
            principal_type="guest",
            principal_id="g1",
            session_id="s1",
            trace_id="t1",
            allowed_tools=frozenset({"runtime.echo"}),
        )
        request = RuntimeRequest(
            message="show workflow status",
            context=context,
            tool_requests=[{"name": "runtime.echo", "params": {"message": "ok"}}],
            top_k=3,
        )
        result = runtime.run(request=request, db=None)
        self.assertIn("STELL-AI", result.reply)
        self.assertTrue(any(evt.agent == "planner" for evt in result.events))
        self.assertTrue(any(evt.agent == "self_eval" for evt in result.events))
        self.assertIn(result.evaluation.status, {"pass", "revised", "needs_attention"})
        self.assertGreaterEqual(len(result.memory.session), 2)

    def test_runtime_compose_reply_surfaces_engineering_summary(self) -> None:
        runtime = StellAIRuntime()

        reply = runtime._compose_reply(
            message="maliyet ve dfm raporu ver",
            retrieval=RetrievalResult(query="maliyet", chunks=[], embedding_dim=0),
            tool_results=[
                ToolExecution(
                    tool_name="dfm_precheck",
                    status="ok",
                    reason=None,
                    output={
                        "recommended_process": "cnc_machining",
                        "capability_status": "supported",
                        "cost_estimate": {"estimated_unit_cost": 42.5, "currency": "EUR"},
                        "dfm_report": {"risk_count": 2},
                    },
                )
            ],
            context_bundle={},
        )

        self.assertIn("Recommended process: cnc_machining", reply)
        self.assertIn("Estimated unit cost: 42.5 EUR", reply)
        self.assertIn("DFM risk count: 2", reply)

    def test_self_evaluator_flags_missing_grounding(self) -> None:
        evaluator = SelfEvaluatorAgent()
        context = RuntimeContext(
            tenant_id="1",
            project_id="p1",
            principal_type="guest",
            principal_id="g1",
            session_id="s1",
            trace_id="t1",
            allowed_tools=frozenset(),
        )
        request = RuntimeRequest(message="summarize current state", context=context, top_k=3)
        retrieval = RetrievalResult(query="summarize current state", chunks=[], embedding_dim=128)
        result = evaluator.evaluate(
            request=request,
            retrieval=retrieval,
            tool_results=[],
            reply="No grounded context was retrieved for this query.",
            context_bundle={"source_references": []},
            retried=False,
        )
        self.assertEqual(result.status, "needs_attention")
        self.assertTrue(result.retry_recommended)
        self.assertIn("no_grounded_evidence", result.issues)

    def test_runtime_retry_re_evaluates_without_recommending_another_retry(self) -> None:
        retrieval_engine = RetrievalEngine(sources=[_InMemorySource([])])
        runtime = StellAIRuntime(
            planner=PlannerAgent(),
            retriever=RetrieverAgent(retrieval_engine),
            researcher=ResearcherAgent(retrieval_engine),
            executor=ExecutorAgent(SafeToolExecutor(allowlist=frozenset())),
            memory_agent=MemoryManagerAgent(MemoryManager(long_term_store=LongTermMemoryStore(tempfile.mkdtemp()))),
        )
        context = RuntimeContext(
            tenant_id="1",
            project_id="p1",
            principal_type="guest",
            principal_id="g1",
            session_id="s1",
            trace_id="t1",
            allowed_tools=frozenset(),
        )
        request = RuntimeRequest(message="summarize current state", context=context, top_k=2)
        result = runtime.run(request=request, db=None)
        self.assertFalse(result.evaluation.retry_recommended)
        self.assertEqual(result.evaluation.status, "needs_attention")
        self.assertIn("retry_completed_but_limit_reached", result.evaluation.actions)
        event_types = [event.event_type for event in result.events if event.agent == "self_eval"]
        self.assertIn("retry_considered", event_types)
        self.assertIn("re_evaluated", event_types)

    def test_runtime_emits_events_to_phase2_bus(self) -> None:
        docs = [
            SourceDocument(
                doc_id="doc1",
                source_type="repository",
                source_ref="docs/one.md",
                text="status context for orchestrator",
                tenant_id=None,
                project_id=None,
            )
        ]
        fake_bus = _FakeEventBus()
        retrieval_engine = RetrievalEngine(sources=[_InMemorySource(docs)])
        runtime = StellAIRuntime(
            planner=PlannerAgent(),
            retriever=RetrieverAgent(retrieval_engine),
            researcher=ResearcherAgent(retrieval_engine),
            executor=ExecutorAgent(SafeToolExecutor(allowlist=frozenset({"runtime.echo"}))),
            memory_agent=MemoryManagerAgent(MemoryManager(long_term_store=LongTermMemoryStore(tempfile.mkdtemp()))),
            event_bus=fake_bus,
        )
        context = RuntimeContext(
            tenant_id="1",
            project_id="p1",
            principal_type="guest",
            principal_id="g1",
            session_id="s1",
            trace_id="t1",
            allowed_tools=frozenset({"runtime.echo"}),
        )
        request = RuntimeRequest(
            message="show status",
            context=context,
            tool_requests=[{"name": "runtime.echo", "params": {"message": "ok"}}],
            top_k=2,
        )
        runtime.run(request=request, db=None)
        self.assertGreaterEqual(len(fake_bus.events), 4)
        event_types = [item["event_type"] for item in fake_bus.events]
        self.assertIn("stellai.runtime.started", event_types)
        self.assertIn("stellai.planner.planned", event_types)
        self.assertIn("stellai.runtime.completed", event_types)


if __name__ == "__main__":
    unittest.main()
