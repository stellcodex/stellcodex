---
archive_schema_version: "10.0"
system: "STELLCODEX"
source_domain: "ARCHIVE"
canonical_status: "ACTIVE_INDEX"
owner_layer: "SYSTEM"
related_release: "V10_CONSTITUTION_ACTIVATION"
hash_sha256: "PENDING"
last_verified_at: "2026-03-16T12:30:00Z"
sync_reference: "ARCHIVE:00_MASTER_INDEX/MASTER_ARCHIVE_INDEX.md"
---

# MASTER_ARCHIVE_INDEX

Primary GitHub authority:
- `docs/v10/00_V10_MASTER_CONSTITUTION.md`
- `docs/v10/01_V10_SOURCE_HIERARCHY.md`

Archive mirror of the master constitution:
- `STELLCODEX_ARCHIVE_ROOT/01_CONSTITUTION_AND_PROTOCOLS/STELLCODEX_V10_ABSOLUTE_SYSTEM_CONSTITUTION.md`

Archive domains:
- `00_MASTER_INDEX`: continuity and operating memory
- `01_CONSTITUTION_AND_PROTOCOLS`: binding constitutions and enforcement rules
- `02_GITHUB_CANON`: repository manifests and release canon
- `03_GDRIVE_ARCHIVE`: Drive mirror manifests and restore evidence
- `04_PRODUCT_SURFACES`: UI maps and product-facing specifications
- `05_CORE_ENGINES`: deterministic pipeline and engine contracts
- `06_OPERATIONS`: release, backup, restore, and runtime procedures
- `07_STELL_AI`: STELL-AI module definitions and evidence rules
- `08_PRODUCT_DATA_MODEL`: entity, schema, and tenancy definitions
- `99_DEPRECATED_AND_FROZEN`: frozen historical material only

Seed manifests:
- `02_GITHUB_CANON/GITHUB_CANON_MANIFEST.md`
- `03_GDRIVE_ARCHIVE/GDRIVE_ARCHIVE_MANIFEST.md`
- `03_GDRIVE_ARCHIVE/DRIVE_REMOTE_INVENTORY_20260316.md`
- `03_GDRIVE_ARCHIVE/RESTORE_PROOF_REGISTER.md`
- `04_PRODUCT_SURFACES/PRODUCT_SURFACE_INDEX.md`
- `05_CORE_ENGINES/CORE_ENGINES_INDEX.md`
- `06_OPERATIONS/RECOVERY_EVIDENCE_20260316.md`
- `06_OPERATIONS/V10_CONSTITUTION_ACTIVATION_EVIDENCE.md`
- `06_OPERATIONS/RELEASE_REGISTER.md`
- `07_STELL_AI/STELL_AI_INDEX.md`
- `08_PRODUCT_DATA_MODEL/PRODUCT_DATA_MODEL_INDEX.md`
- `99_DEPRECATED_AND_FROZEN/DEPRECATION_REGISTER.md`

Continuity files:
- `ARCHIVE_HASH_REGISTER.md`
- `CONTINUATION_CONTEXT.md`
- `CURRENT_STATE.md`
- `ACTIVE_BLOCKERS.md`
- `LAST_PASSING_RELEASE.md`
- `NEXT_ACTION_QUEUE.md`
- `SYSTEM_STATE_LEDGER.md`
- `SYSTEM_COMPONENT_MAP.md`
- `RUNTIME_TO_ARCHIVE_MAP.md`

Conflict resolution:
1. `docs/v10/00_V10_MASTER_CONSTITUTION.md`
2. `docs/v10/01_V10_SOURCE_HIERARCHY.md`
3. repository code
4. runtime evidence and passing tests
5. valid DB, API, and runtime contracts
6. archived historical snapshots
7. prompts
