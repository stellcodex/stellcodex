# Async Snapshot Validation

## Validation Scope

Real validation was run against the live canonical stack. No mocked final claims were used.

## 1. Happy Path

Evidence:

- request file: `scx_638ca39b-6100-4819-8a52-a761e5084c5c`
- run type: `async_snapshot_validation_happy`
- request result: `200 1.007204`
- response returned:
  - `snapshot_job_id = 2d311096-ad9b-460f-8c91-5abc011fb7fc`
  - `drive_snapshot_status = queued`
- later DB state:
  - `2d311096-ad9b-460f-8c91-5abc011fb7fc|uploaded|1|...|2026-03-24 01:04:45+00`

Pass: request returned before Drive upload completed, worker later archived successfully.

## 2. Worker Down

Evidence:

- snapshot worker was intentionally stopped
- request file: `scx_482be220-983d-46b4-8d93-dc2caff5f48f`
- run type: `async_snapshot_validation_worker_down`
- request result: `200 0.484791`
- immediate response:
  - `snapshot_job_id = 24bfd6df-b6ea-47d8-bd5d-c9744a4cec68`
  - `drive_snapshot_status = queued`
- after worker restart:
  - `24bfd6df-b6ea-47d8-bd5d-c9744a4cec68|uploaded|1|...|2026-03-24 01:10:48+00`

Pass: request path remained correct while the worker was down; archival completed later.

## 3. Drive Unavailable / Retry Path

Evidence:

- request file: `scx_fa7a62a3-ae39-4ff6-85b9-eb6fd9b6c3d3`
- run type: `async_snapshot_validation_drive_fail`
- request result: `200 0.235323`
- case id: `9084f29a-768c-4c70-ae55-4d81496735b1`
- snapshot job id: `0e10e9ba-b470-4769-9b40-dba1b351a9e8`
- Drive target was intentionally corrupted to:
  - `missingremote:STELL/.../9084f29a-...json`
- manual worker execution returned:
  - `upload_status = retry_pending`
  - `attempt_count = 1`
  - `last_error = Failed to create file system ... didn't find section in config file`
- after correcting the target and calling retry endpoint:
  - `POST /api/v1/ai/snapshots/jobs/0e10.../retry`
  - final DB state:
    - `0e10e9ba-b470-4769-9b40-dba1b351a9e8|uploaded|2|...|2026-03-24 01:16:59+00`

Pass: failure remained visible, retry/backoff existed, recovery succeeded.

## 4. Duplicate Protection

Evidence:

- backlog case `62128d65-ef31-4f15-9e50-1222bf039412` had multiple queued RQ jobs:
  - `...71e8608d...`
  - `...ccfeb3d...`
  - `...4bd6f607...`
  - plus the new short-format job ids
- snapshot worker processed duplicates
- DB ended in one clean success state:
  - `upload_status = uploaded`
  - `attempt_count = 1`

Pass: duplicate worker pickup did not create duplicate successful archival.

## 5. Local File Missing

Evidence:

- request file: `scx_75b3dfe1-e3d8-4322-a74f-43069a3a3b86`
- run type: `async_snapshot_validation_missing_local`
- request result: `200 0.258892`
- case id: `8204e6a4-da65-4ace-a65f-96c1fa176846`
- snapshot job id: `b5d49a0e-fcd2-486f-af60-d94e7fa0b702`
- local snapshot file was intentionally deleted
- worker result:
  - `retry_pending`
  - `attempt_count = 1`
  - `last_error = local snapshot missing`
- DB state stayed consistent
- local file was then rebuilt from DB truth
- final DB state:
  - `b5d49a0e-fcd2-486f-af60-d94e7fa0b702|uploaded|2|...|2026-03-24 01:24:31+00`

Pass: missing-local failure was visible and recoverable without corrupting case/eval state.

## 6. Tenant Isolation

Live snapshot job rows showed correct tenant-scoped ownership:

- tenant `25` -> missing-local validation
- tenant `26` -> worker-down validation
- tenant `27` -> happy-path / final validation
- tenant `28` -> Drive-failure validation

Pass: no cross-tenant confusion appeared in job state or listing output.

## 7. Self-Learning Continuity

After async cutover, self-learning surfaces still returned live data:

- `GET /api/v1/ai/memory/stats` ->
  - `solved = 10`
  - `failed = 3`
  - `blocked = 7`
  - `recovered = 3`
  - `total_runs = 20`
- `GET /api/v1/ai/eval/summary?limit=5` ->
  - includes async validation cases
- `GET /api/v1/ai/patterns` had already remained consistent during the earlier self-learning validation

Pass: learning records, memory retrieval, and eval continuity were preserved.

## 8. Final Cleaned Runtime Proof

Final post-cleanup request:

- run type: `async_snapshot_validation_final`
- request result: `200 1.693979`
- response returned queued snapshot state immediately
- worker log:
  - started at `01:27:14`
  - `Job OK` at `01:27:41`
- final DB state:
  - `fb79a433-3581-43fc-9a39-d7025074ea15|uploaded|1|...|2026-03-24 01:27:40+00`

Pass: cleaned runtime still behaves correctly after removing the dead sync path.
