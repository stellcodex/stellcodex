# V7 Release 45 App Factory Prompt

Version: 2026.03.07.1
Scope: STELLCODEX V7 application factory (45 modules)
Canonical source paths:
- `/root/workspace/ops/orchestra/state/stellcodex_modules_45.json`
- `/root/workspace/_truth/UI_FLOW_SSOT.md`
- `/root/workspace/_truth/DEPLOYMENT_TOPOLOGY_SSOT.md`
- `/root/workspace/_truth/BACKUP_AND_DRIVE_SYNC_SSOT.md`

## Mission
Generate, validate, and maintain the 45-app STELLCODEX catalog in a deterministic, repeatable release cycle.

## Hard Constraints
- Module count must remain exactly 45.
- Free tier modules: 30 and enabled by default.
- Paid tier modules: 15 and disabled by default.
- Never invent routes, capabilities, or formats outside `stellcodex_modules_45.json`.
- Never emit placeholder claims (`TODO`, fake OAuth connected, fake publish success).
- Never leak secrets in logs, reports, or artifacts.
- If an app cannot run with paid models, degrade to local model path and mark result explicitly as degraded.

## Required Inputs
- Catalog source: `ops/orchestra/state/stellcodex_modules_45.json`
- Runtime health:
  - `GET http://localhost:7010/health`
  - `GET http://localhost:7010/state`
- Evidence root: `/root/stellcodex_output/evidence`
- Report targets:
  - `/root/stellcodex_output/REPORT.md`
  - `/root/stellcodex_output/test_results.json`

## Factory Flow
1. Sync catalog from `stellcodex_modules_45.json`.
2. Validate SSOT files exist and record missing items.
3. Process free modules first, then paid modules.
4. For each module, run model selection using current readiness/quota state.
5. Persist per-module evidence and status (`ok`, `degraded`, `failed`).
6. Run smoke checks for share contract:
   - resolve returns `200`
   - expired returns `410`
   - rate-limit returns `429`
7. Create phase backups (`free`, `paid`, `final`) and upload to configured remote.
8. Write final report and machine-readable test results.

## Output Contract
`test_results.json` must include:
- `generated_at`
- `version`
- `modules.total`, `modules.free`, `modules.paid`
- `modules.completed_free`, `modules.completed_paid`
- `modules.pending_free`, `modules.pending_paid`
- `smoke_test.status`
- `backups[]` with upload result
- `ssot_check.found[]`, `ssot_check.missing[]`

`REPORT.md` must include:
- Source validation summary
- Module inventory summary
- Planning engine summary
- Smoke test summary
- Backup summary
- Evidence samples

## Failure Handling
- If orchestrator readiness is `FAIL`, do not silently pass; report `FAIL` with reason.
- If a model call times out, mark module as degraded and continue cycle.
- If smoke test fails, log explicit `smoke_failed` error with exit code.
- If source files are missing, record `required_source_missing` conflict.

## Acceptance Gate
A cycle is release-gate ready when all are true:
- Catalog sync successful with 45 modules.
- No pending modules remain.
- Smoke test passed.
- Final backup created and upload reported.
- Report and test-results artifacts written.

## Notes
- This file is an SSOT-required release prompt artifact used by 7x24 orchestration checks.
- Changes to this file must preserve the 45-module contract and SSOT references above.
