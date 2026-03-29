# Async Snapshot Cleanup Log

## Cleanup Performed

### 1. Removed Dead Synchronous Upload Path

Deleted from [`backend/app/services/ai_learning.py`](./backend/app/services/ai_learning.py):

- `_write_drive_snapshot(...)`

That function was the old blocking backend-side `rclone` uploader.

### 2. Removed Dead Imports

From the same module:

- removed backend-side `subprocess` dependency for snapshot upload
- removed unused `Path` import tied to the deleted sync uploader

### 3. Backend No Longer Owns Drive Archival Tooling

Cleaned backend image:

- rebuilt backend from canonical compose path
- verified `command -v rclone` inside `stellcodex-backend` returned no path

Result:

- backend no longer carries `rclone`
- only the snapshot worker owns Drive archival execution

### 4. Dedicated Async Worker Left As Canonical Path

Retained:

- `snapshot_worker` service in canonical compose
- `backend/Dockerfile.worker` with `rclone`
- scheduler-driven requeue logic
- admin retry endpoint

## Final Runtime State After Cleanup

`docker ps` showed:

- `stellcodex-backend` healthy
- `stellcodex-snapshot-worker` running
- `stellcodex-worker` running
- no snapshot backlog remaining

## Dead Sync Logic Status

- old sync upload code removed from request path
- backend image no longer has archival tooling
- canonical archival path is async queue + worker only
