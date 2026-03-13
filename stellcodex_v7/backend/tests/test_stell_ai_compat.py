from __future__ import annotations

from types import SimpleNamespace
import unittest

from app.stell_ai import RuntimeContext as LegacyRuntimeContext
from app.stell_ai import RuntimeRequest as LegacyRuntimeRequest
from app.stell_ai import RuntimeResponse as LegacyRuntimeResponse
from app.stell_ai import StellAIRuntime as LegacyStellAIRuntime
from app.stell_ai.listener import _apply_runtime_result_to_task, _build_runtime_request
from app.stell_ai.runtime import execute_channel_runtime as legacy_execute_channel_runtime
from app.stell_ai.runtime import get_stellai_runtime as legacy_get_stellai_runtime
from app.stellai.channel_runtime import execute_channel_runtime
from app.stellai.runtime import StellAIRuntime
from app.stellai.service import get_stellai_runtime
from app.stellai.types import (
    MemorySnapshot,
    PlanNode,
    RetrievalChunk,
    RetrievalResult,
    RuntimeContext,
    RuntimeEvent,
    RuntimeRequest,
    RuntimeResponse,
    SelfEvaluation,
    TaskGraph,
    ToolExecution,
)


class StellAICompatTests(unittest.TestCase):
    def test_legacy_package_exports_primary_runtime_symbols(self) -> None:
        self.assertIs(LegacyStellAIRuntime, StellAIRuntime)
        self.assertIs(legacy_get_stellai_runtime, get_stellai_runtime)
        self.assertIs(legacy_execute_channel_runtime, execute_channel_runtime)
        self.assertIs(LegacyRuntimeContext, RuntimeContext)
        self.assertIs(LegacyRuntimeRequest, RuntimeRequest)
        self.assertIs(LegacyRuntimeResponse, RuntimeResponse)

    def test_build_runtime_request_uses_primary_types(self) -> None:
        task = SimpleNamespace(
            tenant_id=7,
            project_id="demo",
            task_id="task_123",
            trace_id="trace_123",
            goal="analyze geometry status",
        )

        request = _build_runtime_request(
            task=task,
            file_ids=["scx_file_demo"],
            allowed_tools=frozenset({"upload.status", "mesh_analyze"}),
        )

        self.assertIsInstance(request, RuntimeRequest)
        self.assertEqual(request.context.session_id, "task_123")
        self.assertEqual(request.context.file_ids, ("scx_file_demo",))
        self.assertIn("mesh_analyze", request.context.allowed_tools)

    def test_apply_runtime_result_maps_primary_runtime_to_legacy_task_shape(self) -> None:
        task = SimpleNamespace(
            task_id="task_456",
            tenant_id=7,
            project_id="demo",
            trace_id="trace_456",
            goal="show geometry status",
            plan_json=None,
            result_json=None,
            risk_level="low",
            requires_approval="false",
            status="pending",
            error_detail="old error",
        )
        runtime_result = RuntimeResponse(
            session_id="task_456",
            trace_id="trace_456",
            reply="STELL-AI grounded reply",
            plan=TaskGraph.create(
                [
                    PlanNode(node_id="n1", kind="retrieve", description="retrieve"),
                    PlanNode(
                        node_id="n2",
                        kind="execute_tools",
                        description="execute",
                        depends_on=("n1",),
                        payload={"tools": ["upload.status", "mesh_analyze"]},
                    ),
                ],
                metadata={"tool_count": 2},
            ),
            retrieval=RetrievalResult(
                query="show geometry status",
                chunks=[
                    RetrievalChunk(
                        chunk_id="c1",
                        source_type="knowledge",
                        source_ref="docs/geometry.md",
                        text="geometry status guidance",
                        score=0.62,
                    )
                ],
                embedding_dim=96,
            ),
            tool_results=[
                ToolExecution(tool_name="upload.status", status="ok", output={"file_id": "scx_file_demo"}),
                ToolExecution(tool_name="mesh_analyze", status="denied", output={}, reason="tool_not_permitted"),
            ],
            memory=MemorySnapshot(),
            evaluation=SelfEvaluation(status="needs_attention", confidence=0.51, issues=["tool_failures_present"]),
            events=[RuntimeEvent(event_type="planned", agent="planner", payload={"tool_count": 2})],
        )

        _apply_runtime_result_to_task(task=task, runtime_result=runtime_result)

        self.assertEqual(task.status, "partial")
        self.assertEqual(task.risk_level, "low")
        self.assertEqual(task.requires_approval, "false")
        self.assertEqual(task.plan_json["runtime_graph"]["metadata"]["tool_count"], 2)
        self.assertEqual(task.result_json["plan_summary"]["tools"], ["upload.status", "mesh_analyze"])
        self.assertEqual(task.result_json["executed_steps"][0]["tool"], "upload.status")
        self.assertEqual(task.result_json["failed_steps"][0]["error"], "tool_not_permitted")
        self.assertIn("docs/geometry.md", task.result_json["evidence_refs"])
        self.assertIsNone(task.error_detail)


if __name__ == "__main__":
    unittest.main()
