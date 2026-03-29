# Async Snapshot Performance Report

## Baseline

Pre-cutover baseline from [`AI_SELF_LEARNING_REPORT.md`](./AI_SELF_LEARNING_REPORT.md):

- synchronous Orchestra/request wall time: `~18s` to `~31s`

This baseline included blocking Drive archival inside the request path.

## Real Async Request Latencies

Observed request times after async cutover:

| Run Type | Request Time |
|---|---:|
| `async_snapshot_validation_happy` | `1.007204s` |
| `async_snapshot_validation_worker_down` | `0.484791s` |
| `async_snapshot_validation_drive_fail` | `0.235323s` |
| `async_snapshot_validation_missing_local` | `0.258892s` |
| `async_snapshot_validation_final` | `1.693979s` |

Observed range:

- `0.235s` to `1.694s`

## Worker-Side Archival Duration Evidence

Final validation job:

- worker started upload at `01:27:14`
- worker completed at `01:27:41`
- worker-side archival duration: about `27s`

That is within the old synchronous latency band, but it is no longer paid by the request path.

## Queue Behavior

Final live queue stats:

```json
{"disabled":0,"queued":0,"in_progress":0,"retry_pending":0,"failed":0,"uploaded":6,"queue_name":"ai_snapshots","queue_depth":0,"started_count":0,"oldest_pending_age_seconds":null}
```

Steady-state result:

- queue depth `0`
- started count `0`
- no pending or failed rows

## Performance Delta

### User-Facing Path

- before: `~18s` to `~31s`
- after: `~0.24s` to `~1.69s`

### Practical Effect

- Drive archival still takes tens of seconds in some runs
- user-facing request time no longer waits for that archival
- the remaining latency is now mostly DB/local file/enqueue overhead instead of remote archival

## Verdict

The async snapshot pipeline materially reduces request latency while preserving evidence durability and observability. The original bottleneck has been removed from the request path.
