# Async Drive Snapshot Final Report

## 1. Original Synchronous Bottleneck Summary

Before this phase, Drive archival ran inline from the backend request path. Each self-learning case log wrote a local snapshot and then blocked on `rclone mkdir` + `rclone copyto`. Real baseline wall time was about `18s` to `31s`.

## 2. Final Async Architecture

### Request Path

- persist case/eval/memory DB truth
- write local snapshot artifact
- create `ai_snapshot_jobs` row
- enqueue async upload
- return response immediately

### Worker Path

- dedicated `snapshot_worker`
- consume `ai_snapshots`
- claim DB job
- upload local JSON to Drive
- mark `uploaded` or `retry_pending` / `failed`

## 3. DB Schema Changes

New table:

- `ai_snapshot_jobs`

Key fields:

- `snapshot_job_id`
- `case_id`
- `tenant_id`
- `local_snapshot_path`
- `drive_target_path`
- `upload_status`
- `attempt_count`
- `last_error`
- `next_retry_at`
- `uploaded_at`
- `idempotency_key`

Existing `ai_case_logs.drive_snapshot_*` fields remain as compatibility mirrors.

## 4. Request Path Changes

Core request refactor:

- old blocking `_write_drive_snapshot(...)` removed
- request now returns queued state after DB commit + local file + enqueue
- enqueue failure is visible and honest via `503`

Final proof:

- `POST /api/v1/internal/runtime/ai/cases/log`
- response `200 1.693979`
- returned `drive_snapshot_status = queued`
- snapshot later became `uploaded`

## 5. Worker Behavior

Worker responsibilities now include:

- polling due snapshot jobs
- safe DB row claim
- stale lock recovery
- idempotent `rclone copyto --ignore-existing`
- bounded retry/backoff
- terminal failure visibility

Real implementation blockers discovered and fixed:

- overlong RQ job id -> shortened
- shared-worker starvation -> dedicated `snapshot_worker`
- worker cold-start mapper timeout -> bootstrap/prewarm

## 6. Retry / Backoff Model

- max attempts: `5`
- base retry: `10s`
- max retry delay: `300s`
- retry states recorded in DB
- failures are operator-visible and manually retryable

## 7. Observability Surfaces

- `GET /api/v1/ai/snapshots/stats`
- `GET /api/v1/ai/snapshots/jobs`
- `POST /api/v1/ai/snapshots/jobs/{snapshot_job_id}/retry`
- `GET /api/v1/admin/queues`

Final stats:

```json
{"disabled":0,"queued":0,"in_progress":0,"retry_pending":0,"failed":0,"uploaded":6,"queue_name":"ai_snapshots","queue_depth":0,"started_count":0,"oldest_pending_age_seconds":null}
```

## 8. Performance Delta

- old synchronous request wall time: `~18s` to `~31s`
- new async request wall time: `~0.24s` to `~1.69s`

Important nuance:

- worker-side Drive archival can still take roughly `27s`
- that latency is now off the request path

## 9. Known Remaining Limitations

- Drive archival itself is still relatively slow for some uploads
- local snapshot artifacts are retained after upload for durability; local pruning is not yet part of this phase
- Compose warns that `postgres_data` and `minio_data` already exist and could be declared `external: true` later for cleaner infra semantics

## 10. Final Verdict

**READY**

The async Drive snapshot pipeline is production-ready for the current architecture:

- request path no longer blocks on Drive upload
- DB records exact upload state
- retries/backoff are real
- failures are visible and recoverable
- duplicate pickup is safe
- self-learning behavior remains intact
- runtime proof shows materially lower request latency
