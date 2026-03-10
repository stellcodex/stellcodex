from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from uuid import uuid4

os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test_stellcodex")
os.environ.setdefault("JWT_SECRET", "test-secret-key-for-unit-tests-only-32chars!!")

from app.stellai.service import get_stellai_runtime
from app.stellai.types import RuntimeContext, RuntimeRequest


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


def main() -> int:
    parser = argparse.ArgumentParser(description="STELL-AI tool runtime proof runner")
    parser.add_argument("--evidence-dir", default="/root/workspace/evidence/stellai")
    parser.add_argument("--project-id", default="default")
    args = parser.parse_args()

    evidence_dir = Path(args.evidence_dir).resolve()
    evidence_dir.mkdir(parents=True, exist_ok=True)

    fs_root = evidence_dir / "tenant_fs"
    os.environ["STELLAI_TOOL_FS_ROOT"] = str(fs_root)
    os.environ["STELLAI_TOOL_AUDIT_PATH"] = str(evidence_dir / "tool_invocation_audit.jsonl")

    # Ensure lru-cached runtime picks up proof-specific tool paths.
    get_stellai_runtime.cache_clear()
    runtime = get_stellai_runtime()

    tenant_1_root = fs_root / "tenant_1"
    tenant_1_root.mkdir(parents=True, exist_ok=True)
    (tenant_1_root / "data").mkdir(parents=True, exist_ok=True)
    (tenant_1_root / "mesh").mkdir(parents=True, exist_ok=True)
    (tenant_1_root / "data" / "sales.csv").write_text(
        "name,qty,price\nA,5,2.5\nB,10,4.0\nC,20,9.5\n",
        encoding="utf-8",
    )
    (tenant_1_root / "mesh" / "tetra.stl").write_text(_tetra_stl(), encoding="utf-8")

    base_allowed_tools = frozenset(
        {
            "write_file",
            "read_file",
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
            "runtime_status",
        }
    )

    def run_case(*, tenant_id: str, message: str, tools: list[dict]) -> dict:
        context = RuntimeContext(
            tenant_id=str(tenant_id),
            project_id=str(args.project_id),
            principal_type="proof",
            principal_id=f"proof-{tenant_id}",
            session_id=f"proof_{tenant_id}_{uuid4().hex[:10]}",
            trace_id=str(uuid4()),
            allowed_tools=base_allowed_tools,
        )
        request = RuntimeRequest(
            message=message,
            context=context,
            top_k=6,
            tool_requests=tools,
            metadata_filters={"project_id": str(args.project_id)},
        )
        result = runtime.run(request=request, db=None)
        return result.to_dict()

    safe_file_call = run_case(
        tenant_id="1",
        message="safe file tool call",
        tools=[
            {"name": "write_file", "params": {"path": "notes/ops.txt", "content": "hello from tenant1"}},
            {"name": "read_file", "params": {"path": "notes/ops.txt"}},
            {"name": "list_directory", "params": {"path": ".", "recursive": True}},
            {"name": "search_files", "params": {"path": ".", "pattern": "tenant1"}},
        ],
    )

    data_tool_call = run_case(
        tenant_id="1",
        message="data tool call",
        tools=[
            {"name": "csv_reader", "params": {"path": "data/sales.csv"}},
            {"name": "data_summary", "params": {"path": "data/sales.csv"}},
            {
                "name": "data_filter",
                "params": {"path": "data/sales.csv", "filters": [{"column": "qty", "op": "gt", "value": 9}]},
            },
        ],
    )

    cad_tool_call = run_case(
        tenant_id="1",
        message="cad tool call",
        tools=[
            {"name": "mesh_info", "params": {"path": "mesh/tetra.stl"}},
            {"name": "mesh_volume", "params": {"path": "mesh/tetra.stl"}},
            {"name": "mesh_surface_area", "params": {"path": "mesh/tetra.stl"}},
            {"name": "mesh_bounds", "params": {"path": "mesh/tetra.stl"}},
        ],
    )

    research_tool_call = run_case(
        tenant_id="1",
        message="research tool call",
        tools=[
            {"name": "doc_search", "params": {"query": "phase2 event map", "top_k": 4}},
            {"name": "repo_search", "params": {"query": "runtime", "top_k": 4}},
            {"name": "knowledge_lookup", "params": {"query": "audit event", "top_k": 4}},
            {"name": "text_summary", "params": {"query": "phase2 event map"}},
        ],
    )

    denied_action = run_case(
        tenant_id="1",
        message="denied file action",
        tools=[{"name": "read_file", "params": {"path": "../../etc/passwd"}}],
    )

    tenant_isolation = run_case(
        tenant_id="2",
        message="tenant isolation proof",
        tools=[{"name": "read_file", "params": {"path": "../tenant_1/notes/ops.txt"}}],
    )

    artifacts = {
        "tool_safe_file_call.json": safe_file_call,
        "tool_data_call.json": data_tool_call,
        "tool_cad_call.json": cad_tool_call,
        "tool_research_call.json": research_tool_call,
        "tool_denied_action.json": denied_action,
        "tool_tenant_isolation.json": tenant_isolation,
    }

    for name, payload in artifacts.items():
        (evidence_dir / name).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {
        "evidence_dir": str(evidence_dir),
        "audit_log": str(evidence_dir / "tool_invocation_audit.jsonl"),
        "artifacts": sorted(artifacts.keys()),
        "file_case_statuses": [item.get("status") for item in safe_file_call.get("tool_results", [])],
        "data_case_statuses": [item.get("status") for item in data_tool_call.get("tool_results", [])],
        "cad_case_statuses": [item.get("status") for item in cad_tool_call.get("tool_results", [])],
        "research_case_statuses": [item.get("status") for item in research_tool_call.get("tool_results", [])],
        "denied_case": denied_action.get("tool_results", []),
        "tenant_isolation_case": tenant_isolation.get("tool_results", []),
    }
    (evidence_dir / "tool_runtime_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
