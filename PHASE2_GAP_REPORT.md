# PHASE2_GAP_REPORT

## Scope + Guardrails
- Baseline analyzed: `stellcodex_v7` backend/frontend/infrastructure as currently checked out.
- Locked components confirmed and must remain untouched in behavior: orchestrator/state-machine enforcement (`app/core/orchestrator.py`), deterministic rule engine (`app/core/rule_engine.py`), DFM risk engine (`app/core/dfm_engine.py`), and deterministic decision synthesis path (`app/services/orchestrator_engine.py`).
- This report is generated **before** implementation edits per hard gate.

## Current Worker Pipeline
### Primary active upload pipeline
- Entry worker function: `app/workers/tasks.py::convert_file(file_id)`.
- It is currently a monolithic stage-in-function pipeline with internal progress markers:
  - `queued` -> `security` -> `pipeline` -> `finalize` -> `ready`/`failed`.
- Branching by file kind:
  - `3d`: `_pipeline_3d`
  - `2d`: `_pipeline_2d`
  - `doc`: `_pipeline_doc`
  - `image`: `_pipeline_image`

### Legacy parallel worker stack (still present)
- RQ queue workers for old revision-based model:
  - `app/workers/cad_worker.py`
  - `app/workers/drawing_worker.py`
  - `app/workers/render_worker.py`
  - shared artifact helpers in `app/workers/common.py`
- These use `jobs/revisions/artifacts` tables and are not the main upload->ready contract path, but remain part of runtime surface.

## Upload -> Ready Execution Chain (Current)
1. Upload endpoint:
   - `POST /api/v1/files/upload` (`app/api/v1/routes/files.py`).
2. File row creation in `uploaded_files` with `status=queued` and initial metadata.
3. Object write to S3/MinIO.
4. Enqueue `enqueue_convert_file(file_id)` to RQ queue `cad`.
5. RQ worker runs `convert_file(file_id)`:
   - validate extension/mime rules
   - virus scan
   - conversion + artifact generation + metadata writes
   - decision_json build + orchestrator session upsert
   - mark `ready` only if ready contract passes (`assembly_meta` + previews + gltf for 3D)
6. UI polls `GET /api/v1/files/{file_id}/status` until `state=succeeded`.

## Queue / Redis Usage (Current)
- Redis client/queue entrypoint: `app/queue.py`.
- RQ queues in use:
  - `cad`
  - `drawing`
  - `render`
- Worker bootstrap: `app/workers/worker_main.py` (single process consuming all 3 queues).
- Retry currently uses RQ `Retry(max=N)` on enqueue for selected tasks; no explicit stage retry metadata table.
- Redis also used for:
  - share/token probe rate limit counters (`app/api/v1/routes/share.py`)
  - STELL side stream/rpc channels (`app/api/v1/routes/stell.py`, infra bridge).
- Redis Streams are not yet the file processing backbone.

## Existing Job Types
### API-level job types (`/api/v1/jobs`)
- `convert`
- `mesh2d3d`
- `ping`

### Legacy revision job model types (`app/models/core.py`)
- `cad_lod0`
- `cad_lod1`
- `drawing`
- `render`

## Orchestrator Flow (Current)
- Decision generation path:
  - `app/core/orchestrator.py::ensure_session_decision`
  - uses deterministic rules and DFM report generation
  - writes `uploaded_files.decision_json`, `uploaded_files.metadata.decision_json`, `orchestrator_sessions`
- State machine enforcement:
  - `enforce_state_machine` + guard in `upsert_orchestrator_session`
  - canonical S0..S7 progression with anti-skip guard.
- Approval transitions:
  - `app/api/v1/routes/approvals.py` (`approve` / `reject`) enforce policy gates.

## Artifact Generation Points (Current)
- Main upload pipeline artifacts in `app/workers/tasks.py`:
  - 3D: `gltf_key`, `thumbnail_key`, `assembly_meta_key`, inline `assembly_meta`, `preview_jpg_keys`, `geometry_meta_json`, optional `geometry_report` + `dfm_findings`.
  - DOC: `pdf_key`, `thumbnail_key`.
  - 2D/IMAGE: `thumbnail_key`.
- Ready contract guard:
  - `_is_ready_contract` in workers + `_persist_ready_contract_failure` in files route.
- Manifest generation for UI:
  - `_build_scx_manifest` in `app/api/v1/routes/files.py`.

## Frontend State Data Sources (Current)
- Main typed API client: `frontend/services/api.ts`.
- Viewer polling + load flow (`frontend/app/(viewer)/view/[scx_id]/page.tsx`):
  - `getFileStatus(fileId)`
  - `getFile(fileId)`
  - `getFileManifest(fileId)`
- UI currently reads directly from pipeline-backed endpoints (`/files/{id}`, `/files/{id}/status`, `/files/{id}/manifest`, `/files/{id}/decision_json`).
- Part count rendering already derives from `manifest.assembly_tree` / `manifest.part_count` rather than mesh node count.

## System Bottlenecks / Gaps vs Phase-2 Goals
1. Monolithic worker stage execution
- `convert_file` owns all stage transitions; no event-spine orchestration between stages.

2. No artifact manifest cache table
- Artifact reuse is implicit and ad hoc; no canonical `(file_id, version, stage, input_hash)` cache key persistence.

3. Idempotency is partial
- RQ retries exist but there is no `processed_event_ids`, `stage_locks`, or stage-level dedupe table.

4. No DLQ for permanent failures
- Failures logged in `job_failures` and `audit_events`, but no dead-letter queue record + replay workflow.

5. Read model missing
- UI fetches operational tables/endpoints directly; no dedicated projection table for UI-only reads.

6. Event spine not wired to upload chain
- Redis Streams exist elsewhere (`stell`), not for upload pipeline transitions.

7. Versioning cache semantics incomplete
- `file_versions` table exists but upload processing does not consistently bind stage outputs to versioned artifact manifest entries.

8. Grid-ready consumer boundaries not explicit
- Worker tasks are coupled; stage consumers are not isolated by event contract.

## Files Requiring Modification
### New modules required
- `stellcodex_v7/backend/app/core/events.py`
- `stellcodex_v7/backend/app/core/event_bus.py`
- `stellcodex_v7/backend/app/core/event_types.py`
- `stellcodex_v7/backend/app/core/dlq.py`
- `stellcodex_v7/backend/app/workers/consumers/` (new staged consumers)
- `stellcodex_v7/backend/app/core/read_model.py` (projection updater)
- `stellcodex_v7/backend/app/core/artifact_cache.py`
- `stellcodex_v7/backend/app/core/memory_foundation.py`

### Existing backend files to patch
- `app/workers/tasks.py` (decompose monolith into stage event producers/consumers)
- `app/queue.py` (keep RQ; add stream primitives without removing existing queue contract)
- `app/api/v1/routes/files.py` (upload emits initial event + read-model endpoint switch path)
- `app/api/v1/routes/jobs.py` (event-aware status handling where needed)
- `app/api/v1/routes/platform_contract.py` (if job enqueue contract path needs staged route compatibility)
- `app/api/v1/router.py` (register projection/read-model route if introduced)
- `app/models/__init__.py` + new model files (new Phase-2 tables)
- `app/startup.py` (schema bootstrap safety only for new tables, no mutation of locked tables)

### Tests to add/update
- `backend/tests/test_phase2_event_spine.py`
- `backend/tests/test_phase2_idempotency.py`
- `backend/tests/test_phase2_cache_manifest.py`
- `backend/tests/test_phase2_dlq.py`
- `backend/tests/test_phase2_read_model.py`
- preserve and re-run existing contracts (`test_v7_contracts.py`, `test_public_contract_leaks.py`, orchestrator tests)

## Required Migrations
New alembic revision(s) should add, without mutating mandatory V7 tables:
- `artifact_manifest`
  - keys: file_id, version_no, stage, input_hash, artifact_hash, artifact_uri, status, created_at, updated_at
  - unique: `(file_id, version_no, stage)`
- `processed_event_ids`
  - event_id, event_type, consumer, processed_at, trace_id
  - unique: `(event_id, consumer)`
- `stage_locks`
  - file_id, version_no, stage, lock_token, locked_at, expires_at
  - unique: `(file_id, version_no, stage)`
- `dlq_records`
  - id, event_id, type, file_id, version_no, stage, failure_code, error_detail, retry_count, payload_json, created_at
- `file_read_projections` (or equivalent projection table)
  - file_id (public), latest_state, stage_progress, decision_summary, risk_summary, approval_status, timestamps
- optional: `event_log` (if durable DB mirror of stream events is desired for audit/debug).

Mandatory untouched tables (must remain intact):
- `files`, `file_versions`, `jobs`, `job_logs`, `shares`, `audit_events`, `orchestrator_sessions`, `rule_configs`.

## Risk Assessment
### High risk
- Breaking orchestrator/state semantics if stage transitions start mutating state directly.
- Public contract leakage (storage keys/internal IDs) when adding new projection/event payload routes.
- READY regression if assembly_meta gating weakens.

### Medium risk
- Dual-path drift during transition (RQ enqueue path vs stream-driven consumers).
- Duplicate processing under concurrent workers without lock/idempotency enforcement.
- Cache invalidation bugs causing stale artifacts or missed recompute.

### Low risk
- Additional Redis load from streams + consumer groups.
- New projection lag for UI reads.

### Mitigations
- Keep orchestrator as sole state authority; events carry stage facts only.
- Enforce idempotency table + stage lock before stage execution.
- Add strict event envelope schema validation and failure_code taxonomy.
- Preserve legacy endpoints while switching their backing source to projections.
- Extend contract tests for no `storage_key`/`revision_id` exposure.

## Rollback Plan
1. Pre-change snapshot
- DB backup + storage backup using existing release scripts.

2. Deploy rollback toggles
- Feature flag for event-spine consumers (off => current `convert_file` path remains authoritative).
- Feature flag for read-model routing (off => existing direct file queries).

3. Migration rollback
- Down revisions for new Phase-2 tables only; do not touch existing V7 tables.

4. Runtime rollback
- Stop consumer group workers, continue RQ worker monolith.
- Disable stream publish path except audit mirror.

5. Validation after rollback
- Run release gate scripts (`release_gate_v7.sh`) and smoke flow upload->ready->share/approval.

## Phase-2 Execution Readiness
- Hard-gate requirement satisfied: repository analyzed and this gap report created before implementation edits.
- Next execution step per locked order: implement event spine modules and staged pipeline decomposition while preserving locked orchestrator/rule/DFM behavior.
