---
archive_schema_version: "10.0"
system: "STELLCODEX"
source_domain: "GDRIVE"
canonical_status: "ACTIVE_MANIFEST"
owner_layer: "OPERATIONS"
related_release: "V10_CONSTITUTION_ACTIVATION"
hash_sha256: "PENDING"
last_verified_at: "2026-03-16T12:19:07Z"
sync_reference: "ops/scripts/backup-state.sh"
---

# GDRIVE_ARCHIVE_MANIFEST

Configured archive transport:
- `rclone`

Configured Drive root from current backup automation:
- `gdrive:stellcodex-genois`

Expected Drive archive layout from `ops/scripts/backup-state.sh`:
- `backups/db/`
- `backups/config/<timestamp>/`
- `state/`
- `knowledge/`

Expected archive payload classes:
- database dumps
- configuration backups
- orchestra runtime state
- knowledge base mirrors
- canonical context exports
- restore proofs
- audit evidence bundles
- freeze snapshots

Current proof producers:
- `ops/scripts/backup-state.sh` uploads DB, config, state, and knowledge snapshots
- `scripts/weekly_restore_gate.sh` emits restore proof to `evidence/weekly_restore_gate_output.txt`
- `scripts/smoke_gate.sh` emits runtime smoke proof to `evidence/smoke_gate_output.txt`
- `scripts/release_gate.sh` emitted live runtime release proof to `evidence/release_gate_v10_activation_20260316.txt`
- `scripts/object_restore_drill.sh` emits object restore proof to `evidence/object_restore_drill_output.txt`
- `scripts/runtime_restore_probe.sh` emits restore-from-backup runtime proof to `evidence/runtime_restore_probe_output.txt`
- Current recovery evidence mirrored to `gdrive:stellcodex-genois/backups/handoff/V10_RUNTIME_RECOVERY_20260316_111840/`
- Historical passing release evidence mirrored to `gdrive:stellcodex-genois/backups/handoff/V7_STABIL_20260227_EVIDENCE/`
- GitHub V10 canonical context package mirrored to `gdrive:stellcodex-genois/STELLCODEX/01_CANONICAL_CONTEXT/V10_MASTER_PACKAGE/V10_GITHUB_CANONICAL_CONTEXT_20260316_121111/`
- Deterministic recursive inventory captured at `STELLCODEX_ARCHIVE_ROOT/03_GDRIVE_ARCHIVE/DRIVE_RECURSIVE_INVENTORY_20260316.txt`

Registration status:
- Drive root identified: PASS
- Drive folder contract identified: PASS
- Mirrored artifact inventory imported into archive root: PASS
- Full recursive artifact inventory imported into archive root: PASS
- Restore proof mirrored into Drive register: PASS
- Current runtime evidence bundle mirrored into Drive: PASS
- Restore-from-backup runtime probe mirrored into Drive: PASS
- Historical passing release drive mirror registered: PASS
- GitHub V10 canonical context export mirrored into Drive: PASS

Rule:
- Drive proves what happened in the system.
- Any claimed backup or restore event must be traceable to a mirrored artifact set.
- Canonical context exports must remain traceable to the GitHub V10 package and continuity records.
