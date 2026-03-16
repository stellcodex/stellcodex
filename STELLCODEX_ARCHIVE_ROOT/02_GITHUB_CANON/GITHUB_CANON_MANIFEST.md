---
archive_schema_version: "10.0"
system: "STELLCODEX"
source_domain: "GITHUB"
canonical_status: "ACTIVE_MANIFEST"
owner_layer: "ENGINEERING"
related_release: "V10_CONSTITUTION_ACTIVATION"
hash_sha256: "PENDING"
last_verified_at: "2026-03-16T12:30:00Z"
sync_reference: "REPO:/root/workspace"
---

# GITHUB_CANON_MANIFEST

Canonical repository root:
- `/root/workspace`

Canonical code surfaces:
- `backend/`
- `frontend/`
- `db/`
- `docker/`
- `infrastructure/`
- `ops/`
- `scripts/`
- `schemas/`
- `security/`
- `worker.py`

Canonical governance documents:
- `docs/v10/00_V10_MASTER_CONSTITUTION.md`
- `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- `docs/v10/05_V10_API_CONTRACTS.md`
- `docs/v10/10_V10_DEPLOY_BACKUP_RESTORE.md`
- `docs/v10/11_V10_RELEASE_GATES_AND_SMOKE.md`
- `docs/v10/14_V10_DRIVE_ARCHIVE_HIERARCHY.md`
- `docs/v10/15_V10_GITHUB_REPOSITORY_MAP.md`
- `docs/v10/16_V10_CONTEXT_CONTINUATION_PROTOCOL.md`
- `docs/indexes/MASTER_DOC_INDEX.md`
- `docs/manifests/FILE_AUTHORITY_MAP.md`

Operational evidence sources tracked in GitHub:
- `docs/ops/evidence/PHASE_00_BASELINE.md`
- `docs/ops/evidence/PHASE_01_CONTRACT_FREEZE.md`
- `docs/ops/evidence/PHASE_02_DATA_MODEL_RUNTIME.md`
- `docs/ops/evidence/PHASE_03_BACKEND_CONTRACT_SURFACE.md`
- `docs/ops/evidence/PHASE_03_SHARE_CONTRACT_ALIGNMENT.md`
- `docs/ops/evidence/PHASE_04_ADMIN_APPROVALS_UI.md`
- `docs/ops/evidence/PHASE_05_STORAGE_HYGIENE.md`
- `docs/archive/frozen_reports/FINAL_REPORT_20260213.md`
- `docs/archive/frozen_reports/FINAL_EVIDENCE_20260227.md`

Release and restore automation in GitHub:
- `scripts/release_gate.sh`
- `scripts/weekly_restore_gate.sh`
- `scripts/smoke_gate.sh`
- `scripts/backup_db.sh`
- `scripts/backup_object_mirror.sh`
- `scripts/object_restore_drill.sh`
- `scripts/runtime_restore_probe.sh`
- `ops/scripts/backup-state.sh`

Verification note:
- GitHub defines how the system exists.
- Drive and runtime records must resolve back to these canonical repo paths.
