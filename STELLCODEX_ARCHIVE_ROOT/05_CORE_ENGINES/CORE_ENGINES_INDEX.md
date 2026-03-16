---
archive_schema_version: "10.0"
system: "STELLCODEX"
source_domain: "GITHUB"
canonical_status: "ACTIVE_INDEX"
owner_layer: "ENGINEERING"
related_release: "V10_CONSTITUTION_ACTIVATION"
hash_sha256: "PENDING"
last_verified_at: "2026-03-16T11:18:40Z"
sync_reference: "backend/app + scripts/"
---

# CORE_ENGINES_INDEX

Deterministic processing chain:
1. upload
2. convert
3. assembly_meta
4. rule_engine
5. dfm_engine
6. report
7. pack
8. archive

Current repo anchors:
- Upload and file lifecycle: `backend/app/api/v1/routes/files.py`
- Worker conversion and assembly metadata: `backend/app/workers/tasks.py`
- Orchestrator session persistence: `backend/app/services/orchestrator_sessions.py`
- Rule engine and DFM evaluation: `backend/app/core/hybrid_v1_rules.py`, `backend/app/api/v1/routes/dfm.py`
- Approval and share packaging surfaces: `backend/app/api/v1/routes/approvals.py`, `backend/app/api/v1/routes/share.py`
- Archive and backup automation: `scripts/backup_db.sh`, `scripts/backup_object_mirror.sh`, `scripts/object_restore_drill.sh`, `scripts/runtime_restore_probe.sh`, `ops/scripts/backup-state.sh`

Engine rules:
- Jobs must be idempotent.
- Jobs must be traceable.
- Jobs must be recoverable.
