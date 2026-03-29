# Snapshot Worker Implementation

## Runtime Components

- Queue/persistence layer:
  - Redis RQ via [`backend/app/queue.py`](./backend/app/queue.py)
- Snapshot job service:
  - [`backend/app/services/ai_snapshot_jobs.py`](./backend/app/services/ai_snapshot_jobs.py)
- Dedicated worker entrypoint:
  - [`backend/app/workers/snapshot_worker_main.py`](./backend/app/workers/snapshot_worker_main.py)
- Scheduler:
  - [`backend/app/workers/scheduler.py`](./backend/app/workers/scheduler.py)
- Worker bootstrap/prewarm:
  - [`backend/app/workers/bootstrap.py`](./backend/app/workers/bootstrap.py)
- Worker image:
  - [`backend/Dockerfile.worker`](./backend/Dockerfile.worker)
- Canonical runtime service:
  - [`_canonical_repos/infra/deploy/docker-compose.yml`](./_canonical_repos/infra/deploy/docker-compose.yml) `snapshot_worker`

## Worker Algorithm

1. Worker consumes `ai_snapshots`.
2. Claim row with `FOR UPDATE`.
3. Reject if row is already `uploaded` or terminal `failed`.
4. Reject if active lock is still valid.
5. Mark `in_progress`, increment `attempt_count`, stamp `locked_at` / `locked_by`.
6. Validate:
   - drive target exists
   - local snapshot file exists
7. Run:
   - `rclone mkdir <remote dir>`
   - `rclone copyto --ignore-existing <local> <remote>`
8. On success:
   - mark `uploaded`
   - clear lock
   - set `uploaded_at`
9. On failure:
   - mark `retry_pending` or `failed`
   - persist `last_error`
   - schedule `next_retry_at`

## Scheduler Behavior

- Backfills legacy pending snapshot rows once on startup.
- Periodically re-enqueues due `queued` / `retry_pending` rows.
- Reclaims stale `in_progress` locks after timeout.

## Real Runtime Defects Found And Closed

### 1. RQ Job ID Length Overflow

- Symptom: first real request returned `503`
- Cause: generated `last_rq_job_id` exceeded DB column width
- Fix: switched to shorter queue job id format `ai_snapshot:<uuid4hex>`

### 2. Queue Starvation On Shared Worker

- Symptom: snapshot jobs stayed queued while the general worker focused on other queues
- Cause: snapshot archival shared the same worker with CAD/drawing/render load
- Fix:
  - restore general worker to non-snapshot queues
  - add dedicated `snapshot_worker` service for `ai_snapshots`

### 3. Snapshot Worker Cold-Start Timeout

- Symptom: first picked job timed out during lazy SQLAlchemy mapper/config boot
- Fix: add `prepare_worker_runtime()` bootstrap to preload models and configure mappers before `Worker.work()`

## Duplicate Pickup Safety

Live proof existed on backlog case `62128d65-ef31-4f15-9e50-1222bf039412`:

- multiple duplicate RQ jobs were present
- final DB state still became one `uploaded` row with `attempt_count=1`

The worker tolerates duplicate queue pickups because DB state is canonical and remote upload uses `--ignore-existing`.
