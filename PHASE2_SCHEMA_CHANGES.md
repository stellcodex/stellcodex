# PHASE2_SCHEMA_CHANGES

## Migration
- `stellcodex_v7/backend/alembic/versions/i9b8c7d6e5f4_phase2_event_spine_tables.py`
- Revision: `i9b8c7d6e5f4`
- Down revision: `h4d5e6f7a8b9`

## New Tables

### `artifact_manifest`
- Purpose: stage artifact cache/manifest
- Key fields: `file_id`, `version_no`, `stage`, `input_hash`, `artifact_hash`, `artifact_uri`, `artifact_payload`, `status`, `cache_hit_count`
- Constraint: unique `(file_id, version_no, stage)`
- FK: `file_id -> uploaded_files.file_id`

### `processed_event_ids`
- Purpose: idempotency dedupe ledger
- Key fields: `event_id`, `event_type`, `consumer`, `file_id`, `version_no`, `trace_id`, `payload`, `processed_at`
- Constraint: unique `(event_id, consumer)`

### `stage_locks`
- Purpose: per-stage execution lock
- Key fields: `file_id`, `version_no`, `stage`, `lock_token`, `locked_at`, `expires_at`
- Constraint: unique `(file_id, version_no, stage)`

### `dlq_records`
- Purpose: permanent-failure dead letters
- Key fields: `event_id`, `event_type`, `file_id`, `version_no`, `stage`, `failure_code`, `error_detail`, `retry_count`, `payload_json`, `created_at`

### `file_read_projections`
- Purpose: UI read model / projection
- Key fields: `file_id`, `latest_state`, `stage_progress`, `decision_summary`, `risk_summary`, `approval_status`, `status`, `kind`, `mode`, `part_count`, `error_code`, `timestamps`, `payload_json`
- FK: `file_id -> uploaded_files.file_id`

## ORM Additions
- `stellcodex_v7/backend/app/models/phase2.py`
- Imported via `stellcodex_v7/backend/app/models/__init__.py`

## Existing Mandatory Tables (Untouched)
- `files`
- `file_versions`
- `jobs`
- `job_logs`
- `shares`
- `audit_events`
- `orchestrator_sessions`
- `rule_configs`
