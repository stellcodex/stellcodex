# Async Snapshot Model

## Canonical Model

### Request Path

1. Persist canonical case/eval/memory records in Postgres.
2. Generate local JSON snapshot artifact under `AI_MEMORY_LOCAL_SNAPSHOT_DIR`.
3. Create `ai_snapshot_jobs` row with queue-owned archival state.
4. Commit DB state.
5. Enqueue async snapshot upload job.
6. Return response without waiting for Drive upload.

### Async Worker Path

1. Poll or pick queued snapshot jobs from Redis RQ queue `ai_snapshots`.
2. Claim the DB row with lock semantics.
3. Mark row `in_progress`.
4. Upload local snapshot artifact to Drive with `rclone`.
5. On success:
   - mark `uploaded`
   - set `uploaded_at`
   - write Drive path back to case log / memory outcome
6. On failure:
   - mark `retry_pending` or terminal `failed`
   - preserve `last_error`
   - set `next_retry_at` when retryable

## Job Lifecycle

| State | Meaning | Terminal |
|---|---|---|
| `disabled` | Drive archival disabled or no drive target configured | yes |
| `queued` | DB intent persisted, awaiting queue worker | no |
| `in_progress` | Claimed by worker | no |
| `retry_pending` | Upload failed, waiting for backoff window | no |
| `uploaded` | Drive archival completed | yes |
| `failed` | Bounded retries exhausted | yes |

## Idempotency Rules

- One upload job per case: `ai_snapshot_jobs.case_id` is unique.
- Stable idempotency key per case: `ai_case_snapshot:<case_id>`.
- Already uploaded rows are skipped by the worker.
- Worker claim rejects already-uploaded or terminal-failed rows.
- `rclone copyto --ignore-existing` prevents duplicate remote writes from duplicate queue pickup.
- Duplicate queued RQ jobs are tolerated because DB state remains authoritative.

## Retry / Backoff Rules

- Configured in env/settings:
  - `AI_SNAPSHOT_MAX_ATTEMPTS=5`
  - `AI_SNAPSHOT_RETRY_BASE_SECONDS=10`
  - `AI_SNAPSHOT_RETRY_MAX_SECONDS=300`
- Effective backoff sequence:
  - attempt 1 failure -> retry in `10s`
  - attempt 2 failure -> retry in `20s`
  - attempt 3 failure -> retry in `40s`
  - attempt 4 failure -> retry in `80s`
  - capped thereafter by `300s`
- After the bounded attempt limit is reached, state becomes `failed`.

## Failure Visibility

- `ai_snapshot_jobs.last_error`
- `ai_snapshot_jobs.attempt_count`
- `ai_snapshot_jobs.next_retry_at`
- `ai_case_logs.drive_snapshot_status`
- `ai_case_logs.drive_snapshot_error`
- Admin endpoints:
  - `GET /api/v1/ai/snapshots/stats`
  - `GET /api/v1/ai/snapshots/jobs`
  - `POST /api/v1/ai/snapshots/jobs/{snapshot_job_id}/retry`

## Recovery Path

- Retryable failures remain visible as `retry_pending`.
- Operator or scheduler can re-enqueue when the cause is corrected.
- Missing local file is visible and recoverable if the file is rebuilt.
- Drive outage / bad remote path is visible and recoverable after the target is fixed.

## Local Artifact Cleanup Rule

- Local snapshot files are retained after successful upload.
- This is intentional in the current phase: evidence durability is favored over aggressive local deletion.
- Cleanup can be introduced later only if it preserves recoverability and evidence policy.

## Ownership Boundaries

- Backend owns:
  - canonical DB write
  - local snapshot generation
  - upload job creation
- Snapshot worker owns:
  - Drive archival
  - retry/backoff execution
  - upload state transitions
- Drive remains archive truth only.
- No user-facing request waits on `rclone`.
