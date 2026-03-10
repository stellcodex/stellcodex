# PHASE2_PROOF

## 1) Changed File List

### New files
- `PHASE2_GAP_REPORT.md`
- `PHASE2_EVENT_MAP.md`
- `PHASE2_SCHEMA_CHANGES.md`
- `PHASE2_IMPLEMENTATION_LOG.md`
- `PHASE2_PROOF.md`
- `stellcodex_v7/backend/alembic/versions/i9b8c7d6e5f4_phase2_event_spine_tables.py`
- `stellcodex_v7/backend/app/api/v1/routes/approvals.py`
- `stellcodex_v7/backend/app/core/artifact_cache.py`
- `stellcodex_v7/backend/app/core/dlq.py`
- `stellcodex_v7/backend/app/core/event_bus.py`
- `stellcodex_v7/backend/app/core/event_types.py`
- `stellcodex_v7/backend/app/core/events.py`
- `stellcodex_v7/backend/app/core/memory_foundation.py`
- `stellcodex_v7/backend/app/core/read_model.py`
- `stellcodex_v7/backend/app/models/phase2.py`
- `stellcodex_v7/backend/app/workers/consumers/__init__.py`
- `stellcodex_v7/backend/app/workers/consumers/common.py`
- `stellcodex_v7/backend/app/workers/consumers/pipeline.py`
- `stellcodex_v7/backend/tests/test_phase2_event_pipeline.py`

### Modified files
- `stellcodex_v7/backend/app/api/v1/routes/files.py`
- `stellcodex_v7/backend/app/api/v1/routes/platform_contract.py`
- `stellcodex_v7/backend/app/models/__init__.py`
- `stellcodex_v7/backend/app/services/audit.py`
- `stellcodex_v7/backend/app/workers/tasks.py`
- `stellcodex_v7/infrastructure/deploy/scripts/smoke_v7.sh`

## 2) Migration Names
- `i9b8c7d6e5f4_phase2_event_spine_tables.py`

## 3) Test Outputs

### Command
```bash
cd /root/workspace/stellcodex_v7/backend
pytest -q tests/test_phase2_event_pipeline.py tests/test_upload_contracts.py tests/test_public_contract_leaks.py tests/test_master_contract_routes.py tests/test_orchestrator_core.py tests/test_v7_contracts.py tests/test_v7_deterministic_engines.py
```

### Result
- `26 passed, 3 warnings`

## 4) Sample Event Payloads

### `file.uploaded`
```json
{
  "id": "0d7f7a4f-8eb1-4210-9d6f-88eb4fb89d00",
  "type": "file.uploaded",
  "source": "api.files.upload",
  "subject": "scx_file_aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  "tenant_id": "1",
  "project_id": "default",
  "trace_id": "e9a28cd5-d12b-45ad-bd7b-7cbb2c4ecf74",
  "time": "2026-03-08T04:00:00Z",
  "data": {
    "file_id": "scx_file_aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    "version_no": 1,
    "stage": "upload"
  }
}
```

### `job.failed` (DLQ path)
```json
{
  "id": "21d07d88-ea9c-49e8-a11c-27910ea3863f",
  "type": "job.failed",
  "source": "worker.dlq",
  "subject": "scx_file_aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  "tenant_id": "1",
  "project_id": "p1",
  "trace_id": "08b62267-4623-40b7-9cee-02858bf765ef",
  "time": "2026-03-08T04:00:00Z",
  "data": {
    "file_id": "scx_file_aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    "version_no": 1,
    "stage": "convert",
    "failure_code": "CONVERT_FAIL",
    "retry_count": 0
  }
}
```

## 5) Duplicate Event Test (Runtime Proof)
- Test: `Phase2EventPipelineTests.test_duplicate_event_noop`
- File: `stellcodex_v7/backend/tests/test_phase2_event_pipeline.py`
- Assertion: duplicate event returns `status == "duplicate"` and no stage execution.

## 6) Cache Hit Test (Runtime Proof)
- Test: `Phase2EventPipelineTests.test_cache_hit_short_circuit`
- File: `stellcodex_v7/backend/tests/test_phase2_event_pipeline.py`
- Assertion: manifest input hash match returns `status == "cache_hit"`, handler bypassed.

## 7) DLQ Test (Runtime Proof)
- Test: `Phase2EventPipelineTests.test_permanent_failure_goes_to_dlq`
- File: `stellcodex_v7/backend/tests/test_phase2_event_pipeline.py`
- Assertion: permanent stage error writes DLQ path and returns `status == "failed"` with `CONVERT_FAIL`.

## 8) Upload -> Ready Stage Proof
- Test: `Phase2EventPipelineTests.test_upload_to_ready_event_chain`
- File: `stellcodex_v7/backend/tests/test_phase2_event_pipeline.py`
- Assertion:
  - `convert_file(...)` result `status == "ready"`
  - emitted event sequence:
    - `file.uploaded`
    - `file.convert.started`
    - `file.converted`
    - `assembly.ready`
    - `decision.ready`
    - `dfm.ready`
    - `report.ready`
    - `package.ready`

## 9) Smoke Test Proof
- Command: `./infrastructure/deploy/scripts/smoke_test.sh`
- Result: `[smoke] passed` and `[smoke-test] PASS`
- Evidence path (latest gate run):
  - `/root/workspace/evidence/v7_gate_20260308T044122Z/smoke/smoke_test.txt`

## 10) Restore Test Proof
- Executed via: `./infrastructure/deploy/scripts/release_gate_v7.sh` -> `restore.sh`
- Result markers:
  - `[restore] PASS`
  - restore table counts emitted (uploaded_files/orchestrator_sessions/rule_configs/audit_events)
- Evidence path:
  - `/root/workspace/evidence/v7_gate_20260308T044122Z/restore.txt`

## 11) Release Gate Proof
- Command: `./infrastructure/deploy/scripts/release_gate_v7.sh`
- Final result: `[gate] PASS`
- Evidence files:
  - `/root/workspace/evidence/v7_gate_20260308T044122Z/release_gate.log`
  - `/root/workspace/evidence/v7_gate_20260308T044122Z/gate_status.txt` (`PASS`)

## 12) Required Document Presence
- `PHASE2_GAP_REPORT.md` - present
- `PHASE2_EVENT_MAP.md` - present
- `PHASE2_SCHEMA_CHANGES.md` - present
- `PHASE2_IMPLEMENTATION_LOG.md` - present
- `PHASE2_PROOF.md` - present
