# AI Self-Learning Handoff Summary

## Current State

The self-learning loop is live across the canonical runtime:

- `STELL.AI` retrieves prior case memory before deciding
- `Orchestra` logs real execution runs with trace, outcome, error, and duration
- `backend` persists run history, memory tables, eval records, pattern signals, and Drive snapshots
- admin observability endpoints are live and queryable

Validated runtime totals at closure:

- `total_runs = 14`
- `solved = 4`
- `failed = 3`
- `blocked = 7`
- `recovered = 3`
- `not_uploaded = 0`

## Proven Acceptance Points

- Same error is not repeated after 3 runs
  - the `mesh_approx` pattern produced 3 real `execution_error` failures
  - a real `pattern_signal` was generated
  - the same path then shifted into successful guarded runs instead of repeating the prior failure

- Similar problems resolve faster over time
  - the same `mesh_approx` similarity key improved from `321ms` to `201ms`
  - a real `optimization_signal` was generated

- Memory retrieval affects decision payload
  - live decision payloads included `top_similar_cases`, `last_failed_case`, `active_signals`, `memory_required_inputs`, and recovery recommendations

- Eval logs are consistent and queryable
  - verified on:
    - `GET /api/v1/ai/memory/stats`
    - `GET /api/v1/ai/memory/cases?type=failed`
    - `GET /api/v1/ai/eval/summary`
    - `GET /api/v1/ai/patterns`

- Failure to recovery proof exists on real data
  - `mesh_approx` generated `pattern_signal` and `recovery_signal`
  - `brep` required-input and approval path generated a separate real `recovery_signal`

## Only Remaining Operational Note

Drive snapshot upload is still synchronous inside the request path.

Effect:

- correctness is intact
- persistence is complete
- but some Orchestra calls still take roughly `18s-31s` wall-clock time because Postgres write and Drive snapshot export finish before the response returns

This is the only remaining operational note from the current phase.
