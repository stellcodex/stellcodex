# STELLAI_RUNTIME_PROOF

## 1) Execution Date
- UTC execution window: `2026-03-08T06:15:56Z` to `2026-03-08T06:18:xxZ`

## 2) Commands Executed

### Tests
```bash
cd stellcodex_v7/backend
pytest -q tests/test_stellai_runtime.py
pytest -q tests/test_phase2_event_pipeline.py tests/test_orchestrator_core.py
pytest -q tests/test_stellai_runtime.py tests/test_phase2_event_pipeline.py tests/test_orchestrator_core.py > /root/workspace/evidence/stellai/stellai_pytest_20260308T061556Z.txt
```

### Smoke runtime
```bash
cd stellcodex_v7/backend
PYTHONPATH=. python3 scripts/stellai_runtime_smoke.py --message "show workflow status and decision" > /root/workspace/evidence/stellai/stellai_runtime_smoke_20260308T061556Z.json
```

### Permission enforcement proof
```bash
cd stellcodex_v7/backend
DATABASE_URL=... JWT_SECRET=... PYTHONPATH=. python3 <inline> > /root/workspace/evidence/stellai/stellai_permission_enforcement_20260308T061556Z.json
```

### Tenant isolation proof
```bash
cd stellcodex_v7/backend
DATABASE_URL=... JWT_SECRET=... PYTHONPATH=. python3 <inline> > /root/workspace/evidence/stellai/stellai_tenant_isolation_20260308T061556Z.json
```

## 3) Test Results
- File: `evidence/stellai/stellai_pytest_20260308T061556Z.txt`
- Output:
  - `18 passed in 12.24s`

## 4) Runtime Start + Planner Proof
- File: `evidence/stellai/stellai_runtime_smoke_20260308T061556Z.json`
- Proof points:
  - `plan.nodes` includes `retrieve`, `research`, `execute_tools`, `memory_update`
  - `events` includes:
    - `runtime.started`
    - `planner.planned`
    - `runtime.completed`

## 5) Retrieval Activity Proof
- File: `evidence/stellai/stellai_runtime_smoke_20260308T061556Z.json`
- Proof points:
  - `retrieval.embedding_dim = 128`
  - `retrieval.chunks` count > 0 (observed: 5)
  - `retrieval.used_sources` includes `repository`, `artifacts`, `uploads`
  - Top grounded refs present in reply (`PHASE2_GAP_REPORT.md`, `PHASE2_EVENT_MAP.md`, ...)

## 6) Memory Update Proof
- File: `evidence/stellai/stellai_runtime_smoke_20260308T061556Z.json`
- Proof points:
  - `memory.session` contains user + assistant turns
  - `memory.long_term` contains persisted assistant record
  - `memory_path` emitted for long-term entry:
    - `/root/workspace/_truth/records/stell_ai_long_term/tenant_1/default.jsonl`
  - `events` includes `memory.loaded` and `memory.updated`

## 7) Permission Enforcement Proof
- File: `evidence/stellai/stellai_permission_enforcement_20260308T061556Z.json`
- Observed:
  - `runtime.echo` -> `status: ok`
  - `upload.status` -> `status: denied`, `reason: tool_not_permitted_for_request`
- Confirms executor only runs request-permitted + allowlisted actions.

## 8) Tenant Isolation Proof
- File: `evidence/stellai/stellai_tenant_isolation_20260308T061556Z.json`
- Observed:
  - `tenant_1_long_term[*].tenant_id == "1"`
  - `tenant_2_long_term[*].tenant_id == "2"`
- Confirms long-term memory retrieval is tenant-scoped and not cross-leaked.

## 9) Event Pipeline / Orchestrator Integration Proof
- Runtime mirrors agent events through existing event bus integration (`phase2_event_sink`).
- Automated proof in test:
  - `tests/test_stellai_runtime.py::test_runtime_emits_events_to_phase2_bus`
  - validates emitted event types include:
    - `stellai.runtime.started`
    - `stellai.planner.planned`
    - `stellai.runtime.completed`
- Existing phase-2 pipeline/orchestrator tests remain passing in same run.

## 10) Evidence Files
- `evidence/stellai/stellai_runtime_smoke_20260308T061556Z.json`
- `evidence/stellai/stellai_permission_enforcement_20260308T061556Z.json`
- `evidence/stellai/stellai_tenant_isolation_20260308T061556Z.json`
- `evidence/stellai/stellai_runtime_summary_20260308T061556Z.txt`
- `evidence/stellai/stellai_pytest_20260308T061556Z.txt`
