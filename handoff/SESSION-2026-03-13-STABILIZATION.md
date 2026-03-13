# Session 2026-03-13 Stabilization

## Scope

- Scan the current workspace for unfinished, breaking work.
- Restore frontend build and backend contract stability.
- Reduce Git/backup noise on the small host.
- Prevent overlapping heavy operations from clogging the small host.
- Re-check the local deploy stack and release gate end to end after verification.

## Findings

- The primary active breakage was a half-finished workspace routing refactor in `stellcodex_v7/frontend/app/workspace/[workspaceId]/[[...slug]]/page.tsx`.
- That refactor broke both frontend build resolution and backend contract tests that lock the canonical workspace shell.
- Additional TypeScript failures existed in `PlatformClient`, `useFileDetail`, and `useShares`.
- Local dependency artifacts were inflating repo noise:
  - `stellcodex_v7/frontend/node_modules`
  - `stellcodex_v7/frontend/.next`
  - `stellcodex_v7/backend/.venv-engineering`
- The release gate was unsafe for a small server:
  - it could overlap with backup/git/cleanup jobs
  - it defaulted to destructive reset/build behavior
- The visual-only approval contract was failing in smoke because `_stage_pack()` generated `decision_json` while the file status was still `running`, then marked the file `ready`. That persisted stale `S3/PENDING` decisions for visual uploads.

## Fixes Applied

- Restored the canonical workspace route dispatcher and file-open handoff.
- Kept `PlatformClient` aligned with contract tests while fixing nullability issues.
- Hardened hook typing in:
  - `frontend/lib/hooks/useFileDetail.ts`
  - `frontend/lib/hooks/useShares.ts`
- Removed `useSearchParams()` from `WorkspaceRedirect` and switched preserved query handling to `window.location.search` so Next.js 16 static build can complete.
- Updated root `.gitignore` to ignore heavyweight local dependency/build directories for `stellcodex_v7`.
- Added a shared lock helper at `scripts/stellcodex_lock.sh`.
- Hardened these operational scripts so they skip instead of overlapping under load:
  - `scripts/stellcodex_backup_guard.sh`
  - `scripts/stellcodex_git_sync_guard.sh`
  - `scripts/stellcodex_artifact_cleanup.sh`
  - `stellcodex_v7/infrastructure/deploy/scripts/release_gate_v7.sh`
- Changed `release_gate_v7.sh` so the default path no longer forces `down -v` or unconditional image rebuilds.
- Fixed stale approval persistence by moving `f.status = "ready"` before `build_decision_json()` in `backend/app/workers/tasks.py`.
- Hardened orchestrator normalization so stale stored decisions cannot override stricter canonical policy when current file/rule state requires approval.
- Added regression coverage for:
  - stale visual-only `S3` decisions being normalized to approval-required canonical state
  - pack-stage decision generation happening only after status becomes `ready`

## Validation

- Frontend typecheck: `PASS`
- Frontend production build: `PASS`
- Backend pytest suite: `299 passed`
- Targeted regression suite after operational fixes: `46 passed`
- Local backend health after stack recovery:
  - `http://127.0.0.1:18000/api/v1/health` -> `{"status":"ok"}`
- Local frontend:
  - `http://127.0.0.1:3010/` -> `200`
- Public frontend root:
  - `https://stellcodex.com` -> `200`
- Public API:
  - `https://api.stellcodex.com/api/v1/health` -> `{"status":"ok"}`
- WhatsApp local webhook verification:
  - `GET /api/v1/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=stellcodex-local-whatsapp-verify&hub.challenge=321` -> `200`, body `321`
- WhatsApp local webhook runtime:
  - `POST /api/v1/whatsapp/webhook` with `{sender,message}` -> `200`
  - response -> `{"status":"ok","mode":"GENERAL_CHAT","job_id":null,...}`
- Active local deploy containers recovered:
  - `deploy_backend_1`
  - `deploy_worker_1`
  - `deploy_postgres_1`
  - `deploy_minio_1`
  - `deploy_redis_1`
- Full local release gate now passes:
  - evidence: `/root/workspace/evidence/v7_gate_20260313T081247Z`
  - `gate_status.txt` -> `PASS`
  - smoke visual decision -> `S5`, `approval_required=true`
  - approval flow -> reject `200`, approve `200`, final session state `S7`
  - state proof sequence -> `S0,S1,S2,S3,S4,S5,S6,S7`
  - restore verification -> `PASS`
  - backup + storage mirror verification -> `PASS`

## Operational Notes

- `scripts/stellcodex_backup_guard.sh` was observed running and actively syncing with `rclone`, which confirms the Drive backup automation is live.
- Repo-managed timers/scripts for backup, cleanup, and GitHub sync are present under `ops/systemd/` and `scripts/`.
- `scripts/stellcodex_git_sync_guard.sh` was executed successfully:
  - remote: `https://github.com/stellcodex/stellcodex.git`
  - mirror status: `updated`
  - workspace apply status: `skipped_dirty_worktree`
  - tracked changes: `87`
  - untracked changes: `37`
- Backend and worker services were explicitly restarted once after code changes so the bind-mounted source updates were actually loaded into the running processes.
- Drive/export/restore evidence was produced successfully by the final passing gate run.
- WhatsApp runtime verification added:
  - route-level tests now cover verify token, runtime binding, sanitized failure body, and optional Meta signature verification
  - local compose now injects `WHATSAPP_VERIFY_TOKEN`
  - deploy compose and `.env.example` now carry `WHATSAPP_VERIFY_TOKEN` and `WHATSAPP_APP_SECRET`
  - local backend container confirms `WHATSAPP_VERIFY_TOKEN=stellcodex-local-whatsapp-verify`
- Git push/apply was re-evaluated and intentionally not performed:
  - local `master` is already `14` commits ahead of `origin/master`
  - several files touched during stabilization are mixed with broader in-progress user work or exist as untracked new files
  - pushing from the live workspace would therefore risk backing up unrelated unfinished work, not just the stabilization delta

## Remaining Risk

- The local system is now stable and the release gate is green, but GitHub auto-apply/publish is still blocked by the dirty worktree (`tracked_changes=87`, `untracked_changes=37`).
- Public frontend/API endpoints are reachable, but this session did not produce a safe GitHub-backed publish because the repo state is not clean enough for unattended push/apply.
- Public WhatsApp webhook was not verified against a real Meta callback in this session; only the local route, token handshake, runtime binding, and optional signature guard were validated.
