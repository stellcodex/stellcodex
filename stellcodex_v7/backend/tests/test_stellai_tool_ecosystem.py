from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from app.stellai.retrieval import RetrievalEngine, SourceDocument
from app.stellai.tools import SafeToolExecutor, ToolCall
from app.stellai.tools.audit import ToolAuditLogger
from app.stellai.tools.security import ToolSecurityPolicy
from app.stellai.tools_registry import ToolRegistry, register_default_tools
from app.stellai.types import RuntimeContext


class _InMemorySource:
    name = "memory-source"

    def __init__(self, docs: list[SourceDocument]) -> None:
        self.docs = docs

    def collect(self, *, query, context, db, metadata_filters):
        return list(self.docs)


def _context(*, tenant_id: str, allowed_tools: frozenset[str]) -> RuntimeContext:
    return RuntimeContext(
        tenant_id=tenant_id,
        project_id="p1",
        principal_type="guest",
        principal_id=f"guest-{tenant_id}",
        session_id=f"s-{tenant_id}",
        trace_id=f"t-{tenant_id}",
        allowed_tools=allowed_tools,
    )


class StellAIToolEcosystemTests(unittest.TestCase):
    def test_registry_loading_and_lookup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            policy = ToolSecurityPolicy(base_root=tmp_dir)
            docs = [SourceDocument(doc_id="d1", source_type="repository", source_ref="docs/a.md", text="status")]
            registry = ToolRegistry()
            register_default_tools(
                registry,
                retrieval_engine=RetrievalEngine(sources=[_InMemorySource(docs)]),
                security_policy=policy,
            )

            names = {item.name for item in registry.list_tools(include_disabled=True)}
            required = {
                "runtime.echo",
                "system_info",
                "runtime_status",
                "process_status",
                "disk_usage",
                "read_file",
                "write_file",
                "list_directory",
                "search_files",
                "csv_reader",
                "data_summary",
                "data_filter",
                "json_transform",
                "mesh_info",
                "mesh_volume",
                "mesh_surface_area",
                "mesh_bounds",
                "doc_search",
                "repo_search",
                "knowledge_lookup",
                "text_summary",
            }
            self.assertTrue(required.issubset(names))
            read_tool = registry.get_tool("read_file")
            self.assertIsNotNone(read_tool)
            assert read_tool is not None
            self.assertEqual(read_tool.category, "file")
            self.assertEqual(read_tool.permission_scope, "stellai.files.read")
            self.assertGreaterEqual(len(registry.list_tools(category="file")), 4)

    def test_executor_tool_resolution_and_audit_log_creation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            audit_path = Path(tmp_dir) / "audit.jsonl"
            policy = ToolSecurityPolicy(base_root=tmp_dir)
            executor = SafeToolExecutor(
                allowlist=frozenset({"runtime.echo"}),
                security_policy=policy,
                audit_logger=ToolAuditLogger(path=audit_path),
            )
            ctx = _context(tenant_id="1", allowed_tools=frozenset({"runtime.echo"}))
            results = executor.execute_calls(
                context=ctx,
                db=None,
                calls=[
                    ToolCall(name="runtime.echo", params={"message": "ok"}),
                    ToolCall(name="unknown.tool", params={}),
                ],
            )
            self.assertEqual(results[0].status, "ok")
            self.assertEqual(results[1].status, "denied")
            self.assertEqual(results[1].reason, "tool_not_allowlisted")

            lines = [line for line in audit_path.read_text(encoding="utf-8").splitlines() if line.strip()]
            self.assertGreaterEqual(len(lines), 2)
            payloads = [json.loads(line) for line in lines]
            names = [item["tool_name"] for item in payloads]
            self.assertIn("runtime.echo", names)
            self.assertIn("unknown.tool", names)

    def test_file_tools_enforce_permissions_and_path_traversal_rejection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            policy = ToolSecurityPolicy(base_root=tmp_dir)
            executor = SafeToolExecutor(
                allowlist=frozenset({"write_file", "read_file"}),
                security_policy=policy,
                audit_logger=ToolAuditLogger(path=Path(tmp_dir) / "audit.jsonl"),
            )
            ctx = _context(tenant_id="7", allowed_tools=frozenset({"write_file", "read_file"}))

            denied = executor.execute_calls(
                context=ctx,
                db=None,
                calls=[ToolCall(name="write_file", params={"path": "../../etc/passwd", "content": "x"})],
            )
            self.assertEqual(denied[0].status, "denied")
            self.assertIn(denied[0].reason, {"path_outside_tenant_root", "forbidden_path"})

            ok = executor.execute_calls(
                context=ctx,
                db=None,
                calls=[
                    ToolCall(name="write_file", params={"path": "safe/notes.txt", "content": "hello"}),
                    ToolCall(name="read_file", params={"path": "safe/notes.txt"}),
                ],
            )
            self.assertEqual(ok[0].status, "ok")
            self.assertEqual(ok[1].status, "ok")
            self.assertIn("hello", ok[1].output.get("content", ""))

    def test_tenant_isolation_for_file_tools(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            policy = ToolSecurityPolicy(base_root=tmp_dir)
            executor = SafeToolExecutor(
                allowlist=frozenset({"write_file", "read_file"}),
                security_policy=policy,
                audit_logger=ToolAuditLogger(path=Path(tmp_dir) / "audit.jsonl"),
            )
            ctx_1 = _context(tenant_id="1", allowed_tools=frozenset({"write_file", "read_file"}))
            ctx_2 = _context(tenant_id="2", allowed_tools=frozenset({"write_file", "read_file"}))

            write_out = executor.execute_calls(
                context=ctx_1,
                db=None,
                calls=[ToolCall(name="write_file", params={"path": "private/info.txt", "content": "tenant1"})],
            )
            self.assertEqual(write_out[0].status, "ok")

            cross_tenant = executor.execute_calls(
                context=ctx_2,
                db=None,
                calls=[ToolCall(name="read_file", params={"path": "../tenant_1/private/info.txt"})],
            )
            self.assertEqual(cross_tenant[0].status, "denied")
            self.assertEqual(cross_tenant[0].reason, "path_outside_tenant_root")

    def test_data_tool_execution(self) -> None:
        if importlib.util.find_spec("pandas") is None:
            self.skipTest("pandas is not installed")
        with tempfile.TemporaryDirectory() as tmp_dir:
            policy = ToolSecurityPolicy(base_root=tmp_dir)
            allowed = frozenset({"csv_reader", "data_summary", "data_filter", "json_transform"})
            executor = SafeToolExecutor(
                allowlist=allowed,
                security_policy=policy,
                audit_logger=ToolAuditLogger(path=Path(tmp_dir) / "audit.jsonl"),
            )
            ctx = _context(tenant_id="11", allowed_tools=allowed)
            tenant_root = policy.tenant_root(ctx)
            csv_path = tenant_root / "sample.csv"
            csv_path.write_text("name,qty,price\nA,5,2.5\nB,10,4.0\nC,20,9.5\n", encoding="utf-8")

            out = executor.execute_calls(
                context=ctx,
                db=None,
                calls=[
                    ToolCall(name="csv_reader", params={"path": "sample.csv"}),
                    ToolCall(name="data_summary", params={"path": "sample.csv"}),
                    ToolCall(
                        name="data_filter",
                        params={
                            "path": "sample.csv",
                            "filters": [{"column": "qty", "op": "gt", "value": 9}],
                        },
                    ),
                    ToolCall(
                        name="json_transform",
                        params={"operation": "flatten", "data": {"a": 1, "b": {"c": 2}}},
                    ),
                ],
            )
            self.assertEqual(out[0].status, "ok")
            self.assertEqual(out[0].output.get("row_count"), 3)
            self.assertEqual(out[1].status, "ok")
            self.assertEqual(out[2].status, "ok")
            self.assertEqual(out[2].output.get("row_count"), 2)
            self.assertEqual(out[3].status, "ok")
            self.assertEqual(out[3].output.get("data", {}).get("b.c"), 2)

    def test_cad_tool_execution(self) -> None:
        if importlib.util.find_spec("trimesh") is None:
            self.skipTest("trimesh is not installed")
        with tempfile.TemporaryDirectory() as tmp_dir:
            policy = ToolSecurityPolicy(base_root=tmp_dir)
            allowed = frozenset({"mesh_info", "mesh_volume", "mesh_surface_area", "mesh_bounds"})
            executor = SafeToolExecutor(
                allowlist=allowed,
                security_policy=policy,
                audit_logger=ToolAuditLogger(path=Path(tmp_dir) / "audit.jsonl"),
            )
            ctx = _context(tenant_id="12", allowed_tools=allowed)
            tenant_root = policy.tenant_root(ctx)
            mesh_path = tenant_root / "tetra.stl"
            mesh_path.write_text(_tetra_stl(), encoding="utf-8")

            out = executor.execute_calls(
                context=ctx,
                db=None,
                calls=[
                    ToolCall(name="mesh_info", params={"path": "tetra.stl"}),
                    ToolCall(name="mesh_surface_area", params={"path": "tetra.stl"}),
                    ToolCall(name="mesh_bounds", params={"path": "tetra.stl"}),
                ],
            )
            self.assertEqual(out[0].status, "ok")
            self.assertGreater(out[0].output.get("vertex_count", 0), 0)
            self.assertEqual(out[1].status, "ok")
            self.assertGreater(out[1].output.get("surface_area", 0.0), 0.0)
            self.assertEqual(out[2].status, "ok")
            self.assertIn("min", out[2].output)

    def test_research_tool_retrieval_integration(self) -> None:
        docs = [
            SourceDocument(
                doc_id="d1",
                source_type="artifact",
                source_ref="tenant1",
                text="workflow status and safety result",
                tenant_id="1",
                project_id="p1",
            ),
            SourceDocument(
                doc_id="d2",
                source_type="artifact",
                source_ref="tenant2",
                text="workflow status and safety result",
                tenant_id="2",
                project_id="p1",
            ),
        ]
        engine = RetrievalEngine(sources=[_InMemorySource(docs)])
        allowed = frozenset({"doc_search", "text_summary"})
        with tempfile.TemporaryDirectory() as tmp_dir:
            executor = SafeToolExecutor(
                allowlist=allowed,
                retrieval_engine=engine,
                security_policy=ToolSecurityPolicy(base_root=tmp_dir),
                audit_logger=ToolAuditLogger(path=Path(tmp_dir) / "audit.jsonl"),
            )
            ctx = _context(tenant_id="1", allowed_tools=allowed)
            out = executor.execute_calls(
                context=ctx,
                db=None,
                calls=[
                    ToolCall(name="doc_search", params={"query": "workflow status", "top_k": 5}),
                    ToolCall(name="text_summary", params={"query": "workflow status"}),
                ],
            )
            self.assertEqual(out[0].status, "ok")
            refs = [item["source_ref"] for item in out[0].output.get("results", [])]
            self.assertEqual(refs, ["tenant1"])
            self.assertEqual(out[1].status, "ok")
            self.assertTrue(out[1].output.get("summary"))


def _tetra_stl() -> str:
    return """solid tetra
  facet normal 0 0 -1
    outer loop
      vertex 0 0 0
      vertex 1 0 0
      vertex 0 1 0
    endloop
  endfacet
  facet normal 0 -1 0
    outer loop
      vertex 0 0 0
      vertex 0 0 1
      vertex 1 0 0
    endloop
  endfacet
  facet normal -1 0 0
    outer loop
      vertex 0 0 0
      vertex 0 1 0
      vertex 0 0 1
    endloop
  endfacet
  facet normal 1 1 1
    outer loop
      vertex 1 0 0
      vertex 0 0 1
      vertex 0 1 0
    endloop
  endfacet
endsolid tetra
"""


if __name__ == "__main__":
    unittest.main()
