# FINAL_STELL_AUDIT_REPORT

Generated (UTC): 2026-03-06T17:15:42Z
Updated (UTC): 2026-03-06T19:38:21Z

## 1. Summary

- Discovery inventory rows (filtered, in-scope): 856
- Active rows: 242
- Legacy/deprecated rows: 614
- Duplicate hash groups: 61
- Conflict groups: 11
- Files copied into central core tree (unique destinations): 122
- Copy actions logged: 122
- Copy errors: 0

Scope roots covered:
- /root/workspace: 153 rows
- /root/stell: 389 rows
- /var/www/stellcodex: 314 rows

## 2. Inventory

Full machine-readable inventory is stored at:
- `/root/workspace/audit/STELL_SYSTEM_CORE/10_reports/MASTER_PROMPT_INVENTORY.csv`
- `/root/workspace/audit/STELL_SYSTEM_CORE/10_reports/MASTER_PROMPT_INVENTORY.json`

## 3. Duplicates & Conflicts

Detailed conflict report:
- `/root/workspace/audit/STELL_SYSTEM_CORE/10_reports/PROMPT_CONFLICT_REPORT.md`

Key decisions:
- `_truth/STELLCODEX_MASTER_PROMPT_v8.0.md` selected as authoritative over manuals copy.
- V7 constitution selected as authoritative over V6 docs.
- `webhook/main.py` selected as authoritative runtime entrypoint over duplicate `webhook_main.py`.
- STELL runtime loaders (`stell_brain.py`, `stell_ai_memory.py`, `stell_ai_planner.py`) rewired to central manifest resolution.
- Orchestrator runtime prompts (`app.py`, `profiler.py`) now require centralized templates from `STELL_SYSTEM_CORE/.../prompt_templates.json` (strict mode).

## 4. New Central Structure

`/STELL_SYSTEM_CORE` folders created:
- 01_identity
- 02_constitution
- 03_global_policies
- 04_roles
- 05_workers
- 06_tasks
- 07_output_contracts
- 08_tool_policies
- 09_legacy_archive
- 10_reports

## 5. Changes & Fixes

- Built full focused discovery inventory with sha256/snippets.
- Classified files into identity/constitution/policy/role/worker/task/tool/legacy categories.
- Copied active and legacy files into centralized folder tree (local staging + Drive sync target).
- Generated `ACTIVE_PROMPT_MANIFEST.json`, duplicate/conflict JSON artifacts, and copy-action log.
- Applied post-audit runtime rewiring:
  - `/root/stell/stell_brain.py` now resolves prompt/policy sources via `ACTIVE_PROMPT_MANIFEST.json`.
  - `/root/stell/stell_ai_memory.py` now prefers manifest-authoritative markdown sources for indexing.
  - `/root/stell/stell_ai_planner.py` now resolves SSOT read path via manifest map.
- Applied orchestrator prompt externalization:
  - `/root/workspace/ops/orchestra/orchestrator/app.py` now resolves role/review/merge/degraded prompt text via centralized `prompt_templates.json`.
  - `/root/workspace/ops/orchestra/orchestrator/profiler.py` now resolves benchmark prompt sets via centralized `prompt_templates.json`.
- Enforced strict centralized template mode:
  - `ORCHESTRATOR_REQUIRE_EXTERNAL_PROMPTS` defaults to enabled (`1`).
  - Missing/invalid template keys now fail startup or prompt resolution.
- Added these rewired runtime files into `/STELL_SYSTEM_CORE/05_workers/root/stell/` and updated manifest metadata.
- Added centralized template file:
  - `/root/workspace/audit/STELL_SYSTEM_CORE/05_workers/root/workspace/ops/orchestra/orchestrator/prompt_templates.json`
- Added CI prompt drift guard:
  - `/root/stell/scripts/prompt_drift_guard.py`
  - `/root/stell/.github/workflows/ci.yml` updated to run guard on push/PR with full git history (`fetch-depth: 0`).
- Runtime verification executed:
  - PM2 `stell-webhook` restarted with `--update-env`; strict manifest env confirmed in process environment.
  - `/stell/health` endpoint verified `200 OK`.
  - `orchestra_orchestrator_1` strict template path/runtime checks verified against centralized template.
- Monthly recurring audit automation added:
  - Script: `/root/workspace/audit/scripts/monthly_prompt_audit.sh`
  - Cron (UTC): `15 3 1 * *` now runs `/root/workspace/audit/scripts/finalize_provider_audit.sh` (full provider+monthly finalize flow).
  - Includes external ingress reachability checks for active endpoints (`stellcodex.com`, `api.stellcodex.com/api/v1/health`, `stell.stellcodex.com/stell/webhook`); workers.dev check is marked skipped unless provider metadata is available.
- Provider-side live audit automation added:
  - Script: `/root/workspace/audit/scripts/provider_live_audit.sh`
  - Artifacts: `/root/workspace/audit/STELL_SYSTEM_CORE/10_reports/provider/provider_live_audit_*.json|.md`
  - Current live status: `BLOCKED_MISSING_CREDENTIALS` (token-dependent calls not executable yet).
  - Latest provider artifact timestamp: `2026-03-06T19:37:41Z`.
- Provider credential status automation added:
  - Script: `/root/workspace/audit/scripts/provider_credential_status.sh`
  - Artifacts: `/root/workspace/audit/STELL_SYSTEM_CORE/10_reports/provider/provider_credential_status_*.json|.md`
  - Latest credential-status artifact timestamp: `2026-03-06T19:37:29Z`.
- Provider credential onboarding assets added:
  - Template: `/root/workspace/audit/STELL_SYSTEM_CORE/10_reports/provider/PROVIDER_AUDIT_ENV_TEMPLATE.env`
  - Scope guide: `/root/workspace/audit/STELL_SYSTEM_CORE/10_reports/provider/PROVIDER_AUDIT_SCOPE_GUIDE.md`
  - Quickstart helper: `/root/workspace/audit/scripts/provider_live_audit_quickstart.sh`
  - Secure credential file path now prioritized by audit scripts: `/root/workspace/.secrets/provider_audit.env` (`chmod 600`).
- Provider finalize automation added:
  - Script: `/root/workspace/audit/scripts/finalize_provider_audit.sh`
  - Purpose: run provider credential status + provider live audit + monthly audit, then pin latest provider artifact pointers in `ACTIVE_PROMPT_MANIFEST.json` and optionally sync Drive.
  - Produces stable pointer/status files:
    - `/root/workspace/audit/STELL_SYSTEM_CORE/10_reports/provider/LATEST_PROVIDER_LIVE_AUDIT.json`
    - `/root/workspace/audit/STELL_SYSTEM_CORE/10_reports/provider/LATEST_PROVIDER_LIVE_AUDIT.md`
    - `/root/workspace/audit/STELL_SYSTEM_CORE/10_reports/provider/LATEST_PROVIDER_CREDENTIAL_STATUS.json`
    - `/root/workspace/audit/STELL_SYSTEM_CORE/10_reports/provider/LATEST_PROVIDER_CREDENTIAL_STATUS.md`
    - `/root/workspace/audit/STELL_SYSTEM_CORE/10_reports/monthly/LATEST_MONTHLY_AUDIT.md`
    - `/root/workspace/audit/STELL_SYSTEM_CORE/10_reports/provider/PROVIDER_AUDIT_STATUS.json`
- Script snapshots copied into central core:
  - `/root/workspace/audit/STELL_SYSTEM_CORE/10_reports/scripts/monthly_prompt_audit.sh`
  - `/root/workspace/audit/STELL_SYSTEM_CORE/10_reports/scripts/provider_live_audit.sh`
  - `/root/workspace/audit/STELL_SYSTEM_CORE/10_reports/scripts/provider_credential_status.sh`
  - `/root/workspace/audit/STELL_SYSTEM_CORE/10_reports/scripts/provider_live_audit_quickstart.sh`
  - `/root/workspace/audit/STELL_SYSTEM_CORE/10_reports/scripts/finalize_provider_audit.sh`
- External ingress remediation applied:
  - Root cause of `api.stellcodex.com` `502` fixed by aligning nginx upstream to backend bind port (`127.0.0.1:18000`).
  - Patched files with timestamped backups:
    - `/etc/nginx/sites-available/stellcodex-api`
    - `/etc/nginx/sites-enabled/stellcodex`
    - Backup snapshots:
      - `/etc/nginx/sites-available/stellcodex-api.bak.20260306T185354Z`
      - `/etc/nginx/sites-enabled-backups/stellcodex.bak.20260306T185354Z`
  - `nginx -t` and reload successful; external checks now return `200` on required probes.
  - Latest automated ingress verification timestamp: `2026-03-06T19:37:30Z`.

## 6. External Services Audit Notes

- Google Drive: accessible via `rclone` (`gdrive:` remote), existing root `stellcodex-genois` discovered.
- Cloudflare Workers: local worker source and deployment docs found; live provider API enumeration remains blocked (Cloudflare token/account credentials not present in shell env, key env files, or PM2 process env).
- Vercel: active `frontend/vercel.json` discovered and analyzed; live provider API enumeration remains blocked (Vercel token/team credentials not present in shell env, key env files, or PM2 process env).
- DNS: A/AAAA/NS records enumerated for discovered domains (`stellcodex.com`, `api.stellcodex.com`, `stell.stellcodex.com`, workers.dev host).

## 7. High-Risk Findings

- Plain-text secret-bearing `.env` files are present in active paths and historical backups (values intentionally omitted).
- Multiple instruction authorities coexist (`_truth`, `docs/constitution`, `/root/stell/prompts`, and embedded code prompts).
- Runtime ambiguity is substantially reduced via manifest/template-based resolution with strict external template enforcement for orchestrator prompt text.
- Legacy prompt/policy copies in backups and manuals can cause operator confusion if not clearly marked.
- External ingress still partially blind on provider side:
  - Cloudflare/Vercel API credentials are missing, so provider-side route/DNS inventories cannot be continuously verified from API.

## 8. Outstanding Items

- Cloudflare DNS/Worker inventory via provider API remains pending if API token-backed live audit is required.
- Vercel project/env API inventory remains pending if token-backed live audit is required.
- `stell_ai_memory.py` runtime import validation could not be executed end-to-end in this environment because `qdrant_client` is not installed.

## 9. Recommendations

1. Keep `STELL_PROMPT_MANIFEST_PATH` pinned in deployment envs and treat `ACTIVE_PROMPT_MANIFEST.json` as routing source of truth.
2. Keep `prompt_templates.json` under strict change control and block direct prompt drift in runtime code via CI checks.
3. Add CI checks that fail on new duplicate `*prompt*` or `*constitution*` files outside central core.
4. Schedule recurring monthly audit to refresh duplicate/conflict manifests and external endpoint mapping.
5. Rotate exposed secrets and remove plain-text secret files from tracked/deployed directories.
6. Provision read-only Cloudflare and Vercel API credentials dedicated to audit jobs so provider-side drift can be verified continuously.
