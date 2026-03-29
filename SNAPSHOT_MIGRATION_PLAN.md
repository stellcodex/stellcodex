# Snapshot Migration Plan

## Goal

Move new runs to async archival without breaking historical self-learning records.

## Historical Compatibility Rules

- Existing `ai_case_logs` stay intact.
- Existing `ai_eval_results` stay intact.
- Existing memory tables stay intact.
- Existing `AI_SELF_LEARNING_REPORT.md` evidence remains valid.
- Historical runs remain queryable through existing AI endpoints.

## Compatibility Mechanism

Minimal shim: keep snapshot state mirrored on `ai_case_logs` and memory-table outcome JSON while introducing `ai_snapshot_jobs` as the new archival truth.

This avoids breaking:

- memory stats
- eval summary
- pattern signals
- case history browsing

## Legacy Backfill

Implemented helper:

- [`backend/app/services/ai_snapshot_jobs.py`](./backend/app/services/ai_snapshot_jobs.py) `backfill_legacy_snapshot_jobs(...)`

Backfill scope:

- legacy rows with case-log snapshot statuses in:
  - `local_only`
  - `failed`
  - `queued`
  - `retry_pending`
- only when a local snapshot file still exists
- only when Drive archival is configured

## New-Run Rule

- New runs use async job creation only.
- The old synchronous uploader has been removed from `ai_learning.py`.

## Historical Validation Outcome

Historical async validation rows remained queryable after cutover:

- worker-down case
- Drive-failure case
- missing-local case
- happy-path case

They continued to appear correctly in:

- `GET /api/v1/ai/memory/stats`
- `GET /api/v1/ai/eval/summary`
- `GET /api/v1/ai/snapshots/jobs`
