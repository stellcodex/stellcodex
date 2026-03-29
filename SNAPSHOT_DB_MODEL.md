# Snapshot DB Model

## Existing Structured Records Preserved

The async cutover preserves the existing self-learning persistence model:

- `ai_case_logs`
- `ai_eval_results`
- `solved_cases`
- `failed_cases`
- `blocked_cases`
- `recovered_cases`
- `ai_pattern_signals`

The request path still writes those records exactly as before.

## New Dedicated Upload Job Table

The async pipeline adds `ai_snapshot_jobs`.

Live schema proof from Postgres:

| Column | Type | Purpose |
|---|---|---|
| `snapshot_job_id` | `uuid` | primary key |
| `case_id` | `uuid` | unique reference to `ai_case_logs.case_id` |
| `tenant_id` | `bigint` | tenant-scoped ownership |
| `idempotency_key` | `character varying` | stable per-case dedupe key |
| `local_snapshot_path` | `text` | local JSON artifact path |
| `drive_target_path` | `text` | intended Drive target |
| `upload_status` | `character varying` | queue lifecycle state |
| `attempt_count` | `integer` | retry attempt count |
| `last_error` | `text` | last visible failure reason |
| `next_retry_at` | `timestamp with time zone` | retry scheduling |
| `locked_at` | `timestamp with time zone` | in-progress lock timestamp |
| `locked_by` | `character varying` | worker hostname that claimed the row |
| `last_rq_job_id` | `character varying` | last queue job id |
| `uploaded_at` | `timestamp with time zone` | success timestamp |
| `created_at` | `timestamp with time zone` | creation timestamp |
| `updated_at` | `timestamp with time zone` | last mutation timestamp |

## State Truth Rules

- `uploaded=true` style ambiguity is not used.
- Upload truth is the `upload_status` lifecycle plus timestamps.
- `uploaded_at` is only set after actual Drive archival completes.
- `last_error` is preserved on failure and retry states.
- Case log snapshot state is mirrored from the job state so existing self-learning reads remain intact.

## Tenant Isolation

- `tenant_id` is persisted on `ai_snapshot_jobs`.
- API listing joins jobs back to `ai_case_logs`, preserving tenant-correct file/case mapping.
- Validation runs proved multiple tenant IDs in live snapshot rows:
  - tenant `25`
  - tenant `26`
  - tenant `27`
  - tenant `28`

## No Ambiguous Success State

- Request path returns `drive_snapshot_status=queued` immediately after enqueue intent.
- Only the worker can move the state to `uploaded`.
- Failed and retryable states are explicit, queryable, and recoverable.
