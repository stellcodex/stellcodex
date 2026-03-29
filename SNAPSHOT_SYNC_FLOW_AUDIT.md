# Snapshot Sync Flow Audit

## Scope

This audit documents the pre-cutover synchronous Drive archival path that existed before the async snapshot queue + worker pipeline.

## Pre-Cutover Call Graph

1. `POST /api/v1/internal/runtime/ai/cases/log`
2. [`backend/app/api/v1/routes/internal_runtime.py`](./backend/app/api/v1/routes/internal_runtime.py) `log_ai_case(...)`
3. [`backend/app/services/ai_learning.py`](./backend/app/services/ai_learning.py) `record_case_run(...)`
4. [`backend/app/services/ai_learning.py`](./backend/app/services/ai_learning.py) `_snapshot_payload(...)`
5. Old synchronous helper in the same module: `_write_drive_snapshot(...)`
6. Blocking subprocess calls from backend request path:
   - `rclone mkdir <drive date folder>`
   - `rclone copyto <local json> <drive target>`
7. Only after those subprocesses completed did the request finish.

## Blocking Points

- Local JSON snapshot write happened inside the request path.
- Drive folder creation happened inside the request path.
- Drive upload happened inside the request path.
- `rclone` timeout/error handling also happened inside the request path.

## Files / Modules Involved

- [`backend/app/api/v1/routes/internal_runtime.py`](./backend/app/api/v1/routes/internal_runtime.py)
- [`backend/app/services/ai_learning.py`](./backend/app/services/ai_learning.py)
- Backend container image previously carried `rclone` because the backend itself performed archival.

## Pre-Cutover Persistence Model

Existing snapshot state lived only on the case/eval side:

- `ai_case_logs.drive_snapshot_status`
- `ai_case_logs.drive_snapshot_path`
- `ai_case_logs.drive_snapshot_error`
- Mirrored snapshot status/error fields inside memory-table `outcome` JSON

There was no dedicated upload job table, no queue-owned lifecycle, and no bounded retry record per upload attempt.

## Pre-Cutover Failure States

- `rclone` missing in backend runtime -> request completed with local-only archival state
- `rclone copyto` failure -> request carried local-only archival state
- `rclone` timeout -> request carried local-only archival state
- No canonical async retry loop
- No queue-depth or oldest-pending visibility
- No explicit duplicate-pickup protection model

## Duplicate / Retry Characteristics Before Cutover

- No dedicated retry engine existed for snapshot archival.
- No job idempotency key existed for upload attempts.
- A repeated request could recreate or overwrite the same remote snapshot path without a separately tracked archival job state.

## Latency Baseline

Baseline evidence from [`AI_SELF_LEARNING_REPORT.md`](./AI_SELF_LEARNING_REPORT.md):

- Orchestra wall time during synchronous archival: `~18s` to `~31s`

That latency was not core decision/eval time. It was archival time paid directly on the request path.

## Conclusion

The old flow was correct in terms of evidence creation, but operationally wrong for a live self-learning loop because Drive archival sat in the user-facing request path. The async cutover needed to preserve DB truth and local evidence creation while removing `rclone` from the request path entirely.
