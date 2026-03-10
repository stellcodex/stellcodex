# PHASE2_EVENT_MAP

## Event Envelope (Canonical)
```json
{
  "id": "uuid",
  "type": "file.uploaded",
  "source": "api.files.upload",
  "subject": "scx_file_*",
  "tenant_id": "<tenant>",
  "project_id": "<project>",
  "trace_id": "uuid",
  "time": "2026-03-08T04:00:00Z",
  "data": {}
}
```

## Spine Transport
- Redis Streams key: `stellcodex:phase2:events`
- Publisher module: `stellcodex_v7/backend/app/core/event_bus.py`
- Event model: `stellcodex_v7/backend/app/core/events.py`
- Types: `stellcodex_v7/backend/app/core/event_types.py`

## Stage Chain (Locked Order)
1. upload -> `file.uploaded`
2. convert start -> `file.convert.started`
3. convert done -> `file.converted`
4. assembly stage done -> `assembly.ready`
5. deterministic decision done -> `decision.ready`
6. dfm stage done -> `dfm.ready`
7. report stage done -> `report.ready`
8. pack stage done -> `package.ready`

## Consumer Map
- `convert` -> `phase2.consumer.convert` -> `_stage_convert`
- `assembly_meta` -> `phase2.consumer.assembly_meta` -> `_stage_assembly_meta`
- `rule_engine` -> `phase2.consumer.rule_engine` -> `_stage_rule_engine`
- `dfm` -> `phase2.consumer.dfm` -> `_stage_dfm`
- `report` -> `phase2.consumer.report` -> `_stage_report`
- `pack` -> `phase2.consumer.pack` -> `_stage_pack`

## Approval / Failure Events
- Approval required: `approval.required`
- Approval approved: `approval.approved`
- Approval rejected: `approval.rejected`
- Stage failure / DLQ: `job.failed`

## Failure Routing
- Transient error: exponential backoff retry in consumer guard
- Permanent error or retry exhaustion: `dlq_records` write + `job.failed` event emit
- Failure codes:
  - `CONVERT_FAIL`
  - `ASSEMBLY_META_FAIL`
  - `DECISION_FAIL`
  - `DFM_FAIL`
  - `REPORT_FAIL`
  - `PACKAGE_FAIL`
  - `STORAGE_FAIL`
  - `UNKNOWN`

## Control Boundary
- Orchestrator/state machine remains authoritative for decision/state transitions.
- Event spine reports stage facts and workflow transitions only.
