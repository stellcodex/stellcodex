# Snapshot Observability

## Admin / Ops Surfaces

### Snapshot-Specific Endpoints

- `GET /api/v1/ai/snapshots/stats`
- `GET /api/v1/ai/snapshots/jobs?limit=N`
- `POST /api/v1/ai/snapshots/jobs/{snapshot_job_id}/retry`

### Existing Queue Surface Extended

- `GET /api/v1/admin/queues`
- `GET /api/v1/admin/health`

The `ai_snapshots` queue is included in the admin queue set.

## Contract Safety

The snapshot job listing intentionally exposes relative keys, not sensitive raw internals:

- `drive_target_key`
- `local_snapshot_key`

It does not expose:

- raw Drive credentials
- rclone config
- absolute server filesystem paths in the public/admin contract

## Final Live Stats

`GET /api/v1/ai/snapshots/stats` returned:

```json
{"disabled":0,"queued":0,"in_progress":0,"retry_pending":0,"failed":0,"uploaded":6,"queue_name":"ai_snapshots","queue_depth":0,"started_count":0,"oldest_pending_age_seconds":null}
```

## Final Live Job Listing Evidence

Recent uploaded jobs included:

- `fb79a433-3581-43fc-9a39-d7025074ea15` -> final happy-path validation
- `b5d49a0e-fcd2-486f-af60-d94e7fa0b702` -> missing-local recovery validation
- `0e10e9ba-b470-4769-9b40-dba1b351a9e8` -> Drive failure + retry validation
- `24bfd6df-b6ea-47d8-bd5d-c9744a4cec68` -> worker-down validation
- `2d311096-ad9b-460f-8c91-5abc011fb7fc` -> original happy-path validation

Each live row included:

- `snapshot_job_id`
- `case_id`
- `tenant_id`
- `file_id`
- `run_type`
- `final_status`
- `upload_status`
- `attempt_count`
- `last_error`
- `next_retry_at`
- `uploaded_at`
- `drive_target_key`
- `local_snapshot_key`

## Queue Visibility

Final live queue state:

- `rq:queue:ai_snapshots` length = `0`
- worker container `stellcodex-snapshot-worker` is running
- `docker ps` shows dedicated snapshot worker alive independently of the general worker
