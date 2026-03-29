# STELLCODEX — Self-Learning Loop Final Report

**Date:** 2026-03-24
**Scope:** Operational learning from runtime evidence. Not model training.

**Status note (2026-03-29):** This file preserves the 2026-03-24 pre-integration closure state. Its remaining-blockers section is historical only. The current canonical runtime carries STELL.AI and Orchestra from `/root/workspace/_canonical_repos/stell-ai`, `/root/workspace/_canonical_repos/orchestra`, and `/root/workspace/_canonical_repos/infra/deploy/docker-compose.yml`.

---

## Loop Architecture

```
run (STELL.AI / Orchestra)
  │
  ▼
POST /internal/runtime/ai/cases/log          ← case capture + decision log trigger
  │
  ├─► AiCaseLog (DB)                         ← structured case record
  ├─► AiEvalResult (DB)                      ← deterministic eval
  ├─► SolvedCase / FailedCase / BlockedCase / RecoveredCase (DB)   ← typed memory
  ├─► AiPatternSignal (DB)                   ← pattern extraction (auto)
  └─► AiSnapshotJob (DB) → RQ → snapshot_worker → local file → Drive (async)

  ▲
  │
POST /internal/runtime/ai/memory/context     ← retrieval BEFORE next decision
  │
  └─► returns: top_similar_cases, last_failed_case, best_solved_pattern, active_signals
        │
        └─► caller injects into decision payload as retrieved_context_summary
              │
              └─► POST /internal/runtime/ai/cases/log (next run)
                    └─► AiCaseLog.retrieved_context_summary persisted ← LOOP CLOSED
```

---

## Data Model

### `ai_case_logs`
Primary case record. One row per execution.

| Column | Type | Notes |
|---|---|---|
| `case_id` | UUID PK | |
| `tenant_id` | BIGINT | |
| `file_id` | VARCHAR(40) | |
| `project_id` | VARCHAR(128) | |
| `run_type` | VARCHAR(48) | e.g. `dfm_session_sync` |
| `normalized_problem_signature` | TEXT | deterministic JSON of problem shape |
| `similarity_index_key` | VARCHAR(255) | `project_id|kind|mode|status_gate|flags` |
| `input_payload` | JSONB | raw input |
| `decision_output` | JSONB | raw decision |
| `execution_trace` | JSONB | step-by-step trace |
| `final_status` | VARCHAR(16) | `success / failure / blocked` |
| `failure_class` | VARCHAR(32) | `decision_error / infra_error / missing_input / execution_error` |
| `error_trace` | JSONB | structured error |
| `duration_ms` | INTEGER | |
| `retrieved_context_summary` | JSONB | **memory context injected before this run** |
| `drive_snapshot_status` | VARCHAR(16) | `disabled / queued / uploaded / failed` |
| `created_at` | TIMESTAMPTZ | |

### `ai_eval_results`
One eval result per case. Created synchronously with case log.

| Column | Type | Notes |
|---|---|---|
| `case_id` | UUID FK → `ai_case_logs` | |
| `outcome` | VARCHAR(16) | mirrors `final_status` |
| `failure_class` | VARCHAR(32) | |
| `success_rate` | FLOAT | rolling success rate for similar cases |
| `average_resolution_seconds` | FLOAT | |
| `evaluation` | JSONB | full eval dict with `failure_patterns` |

### `solved_cases / failed_cases / blocked_cases / recovered_cases`
Typed memory rows. One row per case. Queryable by `similarity_index_key`.

| Column | Type |
|---|---|
| `case_id` | UUID PK FK → `ai_case_logs` |
| `similarity_index_key` | VARCHAR(255) |
| `decision_taken` | JSONB |
| `outcome` | JSONB |

### `ai_pattern_signals`
Auto-generated. Upserted by `_refresh_signals()` on each run.

| Signal type | Trigger |
|---|---|
| `pattern_signal` | ≥3 failures with same `similarity_index_key` + `failure_class` |
| `recovery_signal` | success after prior failures on same key |
| `optimization_signal` | new fastest resolution (< 90% of prior best) |

### `ai_snapshot_jobs`
Async Drive upload job. One per case log.

### `experience_ledger`
Manual task-level lessons. Written via `/internal/runtime/ai/experience/write`.

### `decision_logs`
Point-in-time decision artifacts. Written via `/internal/runtime/ai/decision-log`.

---

## APIs

### Case Capture
```
POST /internal/runtime/ai/cases/log
X-Internal-Token: <BOOTSTRAP_ADMIN_TOKEN>

{
  "file_id": "scx-...",
  "run_type": "dfm_session_sync",
  "input_payload": {...},
  "decision_output": {...},
  "execution_trace": [...],
  "final_status": "success|failure|blocked",
  "error_trace": {...} | null,
  "duration_ms": 1200,
  "retrieved_context_summary": {...} | null   ← inject memory here
}
```

### Memory Retrieval
```
POST /internal/runtime/ai/memory/context
X-Internal-Token: <BOOTSTRAP_ADMIN_TOKEN>

{
  "file_id": "scx-...",
  "project_id": "...",
  "mode": "brep",
  "geometry_meta": {...},
  "dfm_findings": {...}
}

Response:
{
  "top_similar_cases": [...],
  "last_failed_case": {...},
  "best_solved_pattern": {...},
  "active_signals": [...]
}
```

### Decision Log
```
POST /internal/runtime/ai/decision-log
```

### Admin Inspection (role=admin)
```
GET /ai/memory/stats
GET /ai/memory/cases?type=solved|failed|blocked|recovered|all
GET /ai/eval/summary
GET /ai/patterns
GET /ai/snapshots/stats
GET /ai/snapshots/jobs
POST /ai/snapshots/jobs/{id}/retry
```

---

## Workers / Jobs

| Component | File | Queue |
|---|---|---|
| Snapshot worker | `backend/app/workers/snapshot_worker_main.py` | `ai_snapshots` |
| Snapshot scheduler | `backend/app/workers/scheduler.py:start_snapshot_scheduler` | — |
| Main worker | `backend/app/workers/worker_main.py` | `cad / drawing / render` |

---

## Validation Examples

### solved_case example
```json
{
  "case_id": "...",
  "tenant_id": 1,
  "file_id": "scx-...",
  "run_type": "dfm_session_sync",
  "final_status": "success",
  "failure_class": null,
  "retrieved_context_summary": {
    "top_similar_cases": [...],
    "last_failed_case": {"case_id": "...", "case_type": "failed"},
    "active_signals": [{"signal_type": "pattern_signal", ...}]
  },
  "eval_result": {
    "outcome": "success",
    "success_rate": 0.25,
    "similar_case_count": 4
  },
  "signals": [{"signal_type": "recovery_signal", ...}]
}
```

### failure_case example
```json
{
  "case_id": "...",
  "final_status": "failure",
  "failure_class": "decision_error",
  "eval_result": {
    "outcome": "failure",
    "failure_patterns": [{"failure_class": "decision_error", "count": 1}]
  }
}
```

### recovery_case example
RecoveredCase row appears when `final_status == "success"` AND prior
`failure` or `blocked` runs exist for the same `similarity_index_key`.
The `recovery_signal` is also upserted.

### pattern_signal example
```json
{
  "signal_type": "pattern_signal",
  "similarity_index_key": "validation_project|3d|brep|UNKNOWN|repeat_failure_guard",
  "failure_class": "decision_error",
  "signal_payload": {
    "repeat_count": 3,
    "guard_flag": "repeat_failure_guard",
    "recommended_action": "Require recovery plan input before automatic advance."
  },
  "active": true
}
```

### retrieval-before-next-decision example
Caller flow:
1. Call `POST /internal/runtime/ai/memory/context` → receive `memory_ctx`
2. Pass `memory_ctx` as `retrieved_context_summary` in next `POST /internal/runtime/ai/cases/log`
3. `AiCaseLog.retrieved_context_summary` is persisted → auditable
4. `top_similar_cases` and `active_signals` inside the stored JSON prove what context
   the decision authority had at decision time

---

## Migration

```
alembic upgrade head
```

Migration `c1d2e3f4a5b6` creates all AI learning tables.
`startup.py` also runs `create_all` + column guards on boot (safe for both paths).

---

## Fail-Closed Guarantees

| Failure | Behaviour |
|---|---|
| Snapshot enqueue fails | `SnapshotEnqueueError` raised AFTER case/eval/memory committed. Core case record is safe. |
| `get_memory_context` unavailable | Caller proceeds without context. `retrieved_context_summary` stays null on case log. |
| Drive upload fails | Retried via `AiSnapshotJob` with exponential backoff. Local snapshot kept. |
| DB unavailable during retrieval | Caller catches exception, continues without memory context. |
| Pattern signal extraction fails | Signal not written. Case log is already committed. |

No fake learning. No silent success. Every stored record reflects actual runtime evidence.

---

## Runtime Validation

```bash
cd backend
DATABASE_URL=postgresql://... python scripts/validate_learning_loop.py
```

Checks (24 total):
1. Failure AiCaseLog persisted
2. Failure final_status == 'failure'
3. Failure failure_class == 'decision_error'
4. Failure AiEvalResult persisted
5. Failure eval outcome == 'failure'
6. Failure FailedCase memory row persisted
7. pattern_signal created after 3× repeat failure
8. pattern_signal repeat_count >= 3
9. pattern_signal guard_flag present
10. get_memory_context returns result
11. top_similar_cases populated
12. last_failed_case retrieved
13. active_signals contains pattern_signal
14. Recovery AiCaseLog persisted
15. Recovery final_status == 'success'
16. retrieved_context_summary stored on case log
17. retrieved_context_summary contains top_similar_cases
18. SolvedCase memory row persisted
19. RecoveredCase memory row persisted
20. recovery_signal emitted
21. Blocked AiCaseLog persisted
22. Blocked final_status == 'blocked'
23. BlockedCase memory row persisted
24. get_memory_context with null inputs returns dict (no crash)

---

## Remaining Blockers

| Item | Status |
|---|---|
| STELL.AI integration — must call `/ai/memory/context` before decision and pass result as `retrieved_context_summary` | Pending (STELL.AI side) |
| Drive sync — requires `AI_MEMORY_DRIVE_ENABLED=true` + `AI_MEMORY_DRIVE_ROOT` + rclone remote configured | Config only |
| Pattern-signal-driven decision modification — STELL.AI must read `active_signals` and adjust decision when `guard_flag == repeat_failure_guard` | Pending (STELL.AI side) |
