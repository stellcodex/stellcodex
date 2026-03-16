---
archive_schema_version: "10.0"
system: "STELLCODEX"
source_domain: "GDRIVE"
canonical_status: "ACTIVE_INVENTORY"
owner_layer: "OPERATIONS"
related_release: "V10_CONSTITUTION_ACTIVATION"
hash_sha256: "PENDING"
last_verified_at: "2026-03-16T12:19:07Z"
sync_reference: "rclone lsf gdrive:stellcodex-genois -R + DRIVE_RECURSIVE_INVENTORY_20260316.txt"
---

# DRIVE_REMOTE_INVENTORY_20260316

Verification date:
- `2026-03-16`

Remote root:
- `gdrive:stellcodex-genois`

Observed top-level inventory (`rclone lsf gdrive:stellcodex-genois --max-depth 2`):
- `STELLCODEX/`
- `backups/`
- `knowledge/`
- `state/`
- `stell/`
- `STELLCODEX/01_CANONICAL_CONTEXT/`
- `STELLCODEX/03_EVIDENCE/`
- `STELLCODEX/06_HANDOFF/`
- `backups/config/`
- `backups/db/`
- `backups/handoff/`
- `backups/models/`
- `backups/www/`
- `state/deferred_queue.json`
- `state/model_profiles.json`
- `state/quota_state.json`
- `state/routing_events.jsonl`

Observed recent DB backups (`rclone lsf gdrive:stellcodex-genois/backups/db --max-depth 1 | tail -n 20`):
- `db_20260314_062228.sql.gz`
- `db_20260315_020001.sql.gz`
- `db_20260316_020001.sql.gz`

Observed recent config backups (`rclone lsf gdrive:stellcodex-genois/backups/config --max-depth 1 | tail -n 20`):
- `20260314_062228/`
- `20260315_020001/`
- `20260316_020001/`

Observed handoff evidence bundles (`rclone lsf gdrive:stellcodex-genois/backups/handoff --max-depth 1`):
- `V10_RUNTIME_RECOVERY_20260316_105334/`
- `V10_RUNTIME_RECOVERY_20260316_110545/`
- `V10_RUNTIME_RECOVERY_20260316_111840/`
- `V7_STABIL_20260227_EVIDENCE/`

Observed GitHub canonical context export (`rclone lsf gdrive:stellcodex-genois/STELLCODEX/01_CANONICAL_CONTEXT/V10_MASTER_PACKAGE/V10_GITHUB_CANONICAL_CONTEXT_20260316_121111 -R`):
- `BUNDLE_MANIFEST.txt`
- `README.md`
- `SHA256SUMS.txt`
- `continuity/ACTIVE_BLOCKERS.md`
- `continuity/CONTINUATION_CONTEXT.md`
- `continuity/CURRENT_STATE.md`
- `continuity/NEXT_ACTION_QUEUE.md`
- `docs/indexes/DRIVE_INDEX.md`
- `docs/indexes/LEGACY_INDEX.md`
- `docs/indexes/MASTER_DOC_INDEX.md`
- `docs/indexes/REPO_INDEX.md`
- `docs/manifests/CONSOLIDATION_INVENTORY.md`
- `docs/manifests/DOC_MIGRATION_MANIFEST.md`
- `docs/manifests/FILE_AUTHORITY_MAP.md`
- `docs/manifests/FINAL_CONSOLIDATION_REPORT.md`
- `docs/manifests/LEGACY_RETIREMENT_MANIFEST.md`
- `docs/v10/00_V10_MASTER_CONSTITUTION.md`
- `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- `docs/v10/02_V10_PRODUCT_SCOPE_AND_IDENTITY.md`
- `docs/v10/03_V10_SYSTEM_ARCHITECTURE.md`
- `docs/v10/04_V10_DATA_MODEL.md`
- `docs/v10/05_V10_API_CONTRACTS.md`
- `docs/v10/06_V10_VIEWER_AND_UI_CONTRACT.md`
- `docs/v10/07_V10_SECURITY_LIMITS_AND_COMPLIANCE.md`
- `docs/v10/08_V10_SHARE_AND_PUBLIC_ACCESS_CONTRACT.md`
- `docs/v10/09_V10_ORCHESTRATOR_RULES_AND_DFM.md`
- `docs/v10/10_V10_DEPLOY_BACKUP_RESTORE.md`
- `docs/v10/11_V10_RELEASE_GATES_AND_SMOKE.md`
- `docs/v10/12_V10_OPERATIONS_AND_ADMIN.md`
- `docs/v10/13_V10_EXECUTION_ROADMAP.md`
- `docs/v10/14_V10_DRIVE_ARCHIVE_HIERARCHY.md`
- `docs/v10/15_V10_GITHUB_REPOSITORY_MAP.md`
- `docs/v10/16_V10_CONTEXT_CONTINUATION_PROTOCOL.md`
- `docs/v10/17_V10_LEGACY_RETIREMENT_MAP.md`
- `docs/v10/18_V10_EVIDENCE_AND_MANIFEST_STANDARD.md`
- `docs/v10/19_V10_FRONTEND_SURFACE_CONTRACT.md`
- `docs/v10/20_V10_FINAL_EXECUTION_CHECKLIST.md`

Deterministic recursive inventory artifact:
- local archive copy: `STELLCODEX_ARCHIVE_ROOT/03_GDRIVE_ARCHIVE/DRIVE_RECURSIVE_INVENTORY_20260316.txt`
- SHA-256: `093445218fe3c4489778bf78accc95bae59f71e906c7be6edbf969514ae23cb6`
- total entries: `2708`
- directories: `680`
- files: `2028`
- top-level entry counts:
  - `STELLCODEX`: `46`
  - `backups`: `428`
  - `knowledge`: `63`
  - `state`: `5`
  - `stell`: `2166`

Import status:
- real Drive inventory imported into archive root: PASS
- Drive root contract verified against backup automation: PASS
- current and historical evidence handoff bundles observed: PASS
- GitHub V10 canonical context package exported into Drive: PASS
- full recursive artifact catalog imported: PASS
