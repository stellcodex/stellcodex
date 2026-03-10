# STELLAI_TOOL_RUNTIME_PROOF

## 1) Execution Window
- Date: 2026-03-08 (UTC)
- Evidence root: `/root/workspace/evidence/stellai`

## 2) Commands Run

### Dependency confirmation
```bash
python3 - <<'PY'
import importlib
for m in ['pandas','numpy','trimesh','pyvista']:
    mod=importlib.import_module(m)
    print(m, mod.__version__)
PY
```

### Tests (tool ecosystem + runtime + regression)
```bash
cd /root/workspace/stellcodex_v7/backend
pytest -q tests/test_stellai_tool_ecosystem.py tests/test_stellai_runtime.py tests/test_phase2_event_pipeline.py tests/test_orchestrator_core.py \
  > /root/workspace/evidence/stellai/stellai_tool_pytest_20260308T070742Z.txt
```

### Live runtime tool proof (runtime smoke path)
```bash
cd /root/workspace/stellcodex_v7/backend
PYTHONPATH=. python3 scripts/stellai_tool_runtime_proof.py --evidence-dir /root/workspace/evidence/stellai
```

### Registry snapshot proof
```bash
cd /root/workspace/stellcodex_v7/backend
DATABASE_URL=postgresql://test:test@localhost:5432/test_stellcodex \
JWT_SECRET=test-secret-key-for-unit-tests-only-32chars!! \
PYTHONPATH=. python3 - <<'PY' > /root/workspace/evidence/stellai/tool_registry_snapshot.json
from app.stellai.tools import SafeToolExecutor
import json
ex=SafeToolExecutor()
print(json.dumps({'tool_count': len(ex.list_tools()), 'tools': ex.list_tools(), 'allowlist': sorted(list(ex.allowlist))}, indent=2))
PY
```

## 3) Test Output Proof
Evidence:
- `/root/workspace/evidence/stellai/stellai_tool_pytest_20260308T070742Z.txt`

Result:
- `25 passed in 18.19s`

## 4) Tool Invocation Proof (Live Runtime)
Runtime summary evidence:
- `/root/workspace/evidence/stellai/tool_runtime_summary.json`

Observed status summary:
- `file_case_statuses`: `ok, ok, ok, ok`
- `data_case_statuses`: `ok, ok, ok`
- `cad_case_statuses`: `ok, ok, ok, ok`
- `research_case_statuses`: `ok, ok, ok, ok`

### 4.1 Safe file tool call
Evidence:
- `/root/workspace/evidence/stellai/tool_safe_file_call.json`

Verified tools executed via runtime:
- `write_file`
- `read_file`
- `list_directory`
- `search_files`

### 4.2 Data tool call
Evidence:
- `/root/workspace/evidence/stellai/tool_data_call.json`

Verified tools executed via runtime:
- `csv_reader`
- `data_summary`
- `data_filter`

### 4.3 CAD tool call
Evidence:
- `/root/workspace/evidence/stellai/tool_cad_call.json`

Verified tools executed via runtime:
- `mesh_info`
- `mesh_volume`
- `mesh_surface_area`
- `mesh_bounds`

### 4.4 Research/retrieval tool call
Evidence:
- `/root/workspace/evidence/stellai/tool_research_call.json`

Verified tools executed via runtime:
- `doc_search`
- `repo_search`
- `knowledge_lookup`
- `text_summary`

## 5) Denied / Blocked Action Proof
Evidence:
- `/root/workspace/evidence/stellai/tool_denied_action.json`

Observed:
- Tool: `read_file`
- Input path: `../../etc/passwd`
- Result: `status=denied`
- Reason: `path_outside_tenant_root`

## 6) Tenant Isolation Proof
Evidence:
- `/root/workspace/evidence/stellai/tool_tenant_isolation.json`

Observed:
- Tenant `2` attempted `read_file` on `../tenant_1/notes/ops.txt`
- Result: `status=denied`
- Reason: `path_outside_tenant_root`

## 7) Executor/Tool Interaction Proof
Evidence:
- `/root/workspace/evidence/stellai/tool_safe_file_call.json`
- `/root/workspace/evidence/stellai/tool_data_call.json`

Observed runtime plan structure includes `execute_tools` node with requested tool names, proving planner -> executor -> registry path:
- `plan.nodes[].kind` contains `execute_tools`
- `plan.nodes[].payload.tools` includes invoked tool list
- `tool_results[]` contains structured per-tool outputs

## 8) Audit Logging Proof
Evidence:
- `/root/workspace/evidence/stellai/tool_invocation_audit.jsonl`

Observed audit records include:
- successful tool calls (`status=ok`) across file/data/CAD/research categories
- denied actions (`status=denied`) for blocked traversal/tenant-cross attempts
- tenant/session/trace metadata per invocation

## 9) Artifact Index
- `/root/workspace/evidence/stellai/tool_registry_snapshot.json`
- `/root/workspace/evidence/stellai/tool_dependency_versions.json`
- `/root/workspace/evidence/stellai/tool_invocation_audit.jsonl`
- `/root/workspace/evidence/stellai/tool_safe_file_call.json`
- `/root/workspace/evidence/stellai/tool_data_call.json`
- `/root/workspace/evidence/stellai/tool_cad_call.json`
- `/root/workspace/evidence/stellai/tool_research_call.json`
- `/root/workspace/evidence/stellai/tool_denied_action.json`
- `/root/workspace/evidence/stellai/tool_tenant_isolation.json`
- `/root/workspace/evidence/stellai/tool_runtime_summary.json`
- `/root/workspace/evidence/stellai/stellai_tool_pytest_20260308T070742Z.txt`
