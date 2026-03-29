# Request Path Refactor Log

## Refactor Goal

Remove Drive archival from the synchronous request path without changing case/eval/memory correctness.

## Changed Request-Path Behavior

### Before

- `record_case_run(...)` wrote DB state
- generated JSON snapshot
- uploaded to Drive inline from backend
- request waited for `rclone`

### After

- `record_case_run(...)` writes DB case/eval/memory state
- generates local JSON snapshot
- creates `ai_snapshot_jobs` row
- commits DB truth
- enqueues async upload job
- returns immediately

## Primary Files Changed

- [`backend/app/services/ai_learning.py`](./backend/app/services/ai_learning.py)
- [`backend/app/services/ai_snapshot_jobs.py`](./backend/app/services/ai_snapshot_jobs.py)
- [`backend/app/api/v1/routes/internal_runtime.py`](./backend/app/api/v1/routes/internal_runtime.py)
- [`backend/app/models/ai_learning.py`](./backend/app/models/ai_learning.py)
- [`backend/app/models/__init__.py`](./backend/app/models/__init__.py)
- [`backend/app/startup.py`](./backend/app/startup.py)

## Enqueue Failure Semantics

- If DB commit succeeds but queue enqueue fails, the request does not fake upload success.
- The job is moved to `retry_pending` with visible error.
- The route raises `503` through `SnapshotEnqueueError`.
- Snapshot intent is not lost because the DB row already exists.

## Final Live Request Proof

Final cleaned-runtime request:

- endpoint: `POST /api/v1/internal/runtime/ai/cases/log`
- file: `scx_638ca39b-6100-4819-8a52-a761e5084c5c`
- run type: `async_snapshot_validation_final`
- response: `200 1.693979`
- response body included:
  - `snapshot_job_id = fb79a433-3581-43fc-9a39-d7025074ea15`
  - `drive_snapshot_status = queued`
  - `drive_snapshot_path = null`

That is the required behavior: correct DB write and immediate response without waiting for Drive upload.
