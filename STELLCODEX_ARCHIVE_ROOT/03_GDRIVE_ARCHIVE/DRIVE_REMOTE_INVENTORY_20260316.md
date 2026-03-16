---
archive_schema_version: "10.0"
system: "STELLCODEX"
source_domain: "GDRIVE"
canonical_status: "ACTIVE_INVENTORY"
owner_layer: "OPERATIONS"
related_release: "V10_CONSTITUTION_ACTIVATION"
hash_sha256: "PENDING"
last_verified_at: "2026-03-16T11:18:40Z"
sync_reference: "rclone lsf gdrive:stellcodex-genois"
---

# DRIVE_REMOTE_INVENTORY_20260316

Verification date:
- `2026-03-16`

Remote root:
- `gdrive:stellcodex-genois`

Observed top-level inventory (`rclone lsf gdrive:stellcodex-genois --max-depth 2`):
- `backups/`
- `knowledge/`
- `state/`
- `stell/`
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

Import status:
- real Drive inventory imported into archive root: PASS
- Drive root contract verified against backup automation: PASS
- current and historical evidence handoff bundles observed: PASS
- full recursive artifact catalog imported: NO
