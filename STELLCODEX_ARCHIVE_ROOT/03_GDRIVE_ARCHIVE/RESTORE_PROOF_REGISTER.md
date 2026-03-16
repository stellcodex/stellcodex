---
archive_schema_version: "10.0"
system: "STELLCODEX"
source_domain: "GDRIVE"
canonical_status: "ACTIVE_REGISTER"
owner_layer: "OPERATIONS"
related_release: "V10_CONSTITUTION_ACTIVATION"
hash_sha256: "PENDING"
last_verified_at: "2026-03-16T11:18:40Z"
sync_reference: "scripts/weekly_restore_gate.sh + scripts/object_restore_drill.sh + scripts/runtime_restore_probe.sh"
---

# RESTORE_PROOF_REGISTER

Registered restore proof producer:
- `scripts/weekly_restore_gate.sh`
- `scripts/object_restore_drill.sh`
- `scripts/runtime_restore_probe.sh`

Expected evidence output:
- `evidence/weekly_restore_gate_output.txt`
- `evidence/object_restore_drill_output.txt`
- `evidence/runtime_restore_probe_output.txt`

Current restore proof coverage required by V10:
- database recovery: PASS on `2026-03-16` via restore into `stellcodex_restore_probe`
- object storage recovery: PASS on `2026-03-16` via `scripts/object_restore_drill.sh` against isolated MinIO probe
- worker recovery: PASS on `2026-03-16` via `scripts/runtime_restore_probe.sh` against restored DB + mirrored object storage + isolated Redis/worker
- API recovery: PASS on `2026-03-16` via `scripts/runtime_restore_probe.sh` against restored DB + mirrored object storage + isolated backend

Current status:
- restore automation script exists: PASS
- imported restore proof artifact exists in archive root: YES (`/root/workspace/evidence/weekly_restore_gate_output.txt`)
- imported smoke proof artifact exists in archive root: YES (`/root/workspace/evidence/smoke_gate_output.txt`)
- imported object restore proof artifact exists in archive root: YES (`/root/workspace/evidence/object_restore_drill_output.txt`)
- imported runtime restore probe artifact exists in archive root: YES (`/root/workspace/evidence/runtime_restore_probe_output.txt`)
- Drive mirror reference for restore proof exists: YES (`gdrive:stellcodex-genois/backups/handoff/V10_RUNTIME_RECOVERY_20260316_111840/weekly_restore_gate_output.txt`)
- Drive mirror reference for smoke proof exists: YES (`gdrive:stellcodex-genois/backups/handoff/V10_RUNTIME_RECOVERY_20260316_111840/smoke_gate_output.txt`)
- Drive mirror reference for release proof exists: YES (`gdrive:stellcodex-genois/backups/handoff/V10_RUNTIME_RECOVERY_20260316_111840/release_gate_v10_activation_20260316.txt`)
- Drive mirror reference for object restore proof exists: YES (`gdrive:stellcodex-genois/backups/handoff/V10_RUNTIME_RECOVERY_20260316_111840/object_restore_drill_output.txt`)
- Drive mirror reference for runtime restore proof exists: YES (`gdrive:stellcodex-genois/backups/handoff/V10_RUNTIME_RECOVERY_20260316_111840/runtime_restore_probe_output.txt`)
- Drive mirror reference for current recovery bundle exists: YES (`gdrive:stellcodex-genois/backups/handoff/V10_RUNTIME_RECOVERY_20260316_111840/`)

Latest evidence:
- restore attempt evidence: `/root/workspace/evidence/weekly_restore_gate_output.txt`
- smoke gate evidence: `/root/workspace/evidence/smoke_gate_output.txt`
- runtime release evidence: `/root/workspace/evidence/release_gate_v10_activation_20260316.txt`
- object restore evidence: `/root/workspace/evidence/object_restore_drill_output.txt`
- runtime restore probe evidence: `/root/workspace/evidence/runtime_restore_probe_output.txt`
- local DB dump: `/root/workspace/backups/db_stellcodex_20260316_124352.sql.gz`
- local object mirror: `/root/workspace/backups/object_mirror/stellcodex`
- Drive recovery bundle: `gdrive:stellcodex-genois/backups/handoff/V10_RUNTIME_RECOVERY_20260316_111840/`

Rule:
- Archive-local and Drive-mirrored restore proof are PASS across database, object storage, worker, and API recovery.
