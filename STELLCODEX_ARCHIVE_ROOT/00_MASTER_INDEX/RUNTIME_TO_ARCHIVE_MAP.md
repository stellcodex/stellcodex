---
archive_schema_version: "10.0"
system: "STELLCODEX"
source_domain: "ARCHIVE"
canonical_status: "ACTIVE_MAP"
owner_layer: "OPERATIONS"
related_release: "V10_CONSTITUTION_ACTIVATION"
hash_sha256: "PENDING"
last_verified_at: "2026-03-16T12:19:07Z"
sync_reference: "ARCHIVE:00_MASTER_INDEX/RUNTIME_TO_ARCHIVE_MAP.md"
---

# RUNTIME_TO_ARCHIVE_MAP

Runtime to archive mapping:
- Source code and infra definitions -> `02_GITHUB_CANON`
- Release manifests and gate outputs -> `02_GITHUB_CANON` and `06_OPERATIONS`
- Backups, restore proofs, exports, audit bundles -> `03_GDRIVE_ARCHIVE`
- Product UI definitions and route maps -> `04_PRODUCT_SURFACES`
- Deterministic pipeline and engine contracts -> `05_CORE_ENGINES`
- Operational runbooks, backup, restore, release procedures -> `06_OPERATIONS`
- STELL-AI behavior and evidence controls -> `07_STELL_AI`
- Schema and entity definitions -> `08_PRODUCT_DATA_MODEL`
- Frozen legacy material -> `99_DEPRECATED_AND_FROZEN`

Current registered producers:
- `scripts/release_gate.sh` -> release gate outputs under `06_OPERATIONS`
- `scripts/weekly_restore_gate.sh` -> restore proof records under `03_GDRIVE_ARCHIVE` and `06_OPERATIONS`
- `ops/scripts/backup-state.sh` -> Drive mirror payloads under `03_GDRIVE_ARCHIVE`
- `docs/v10/`, `docs/indexes/`, `docs/manifests/`, and root `README.md` -> canonical context export under `03_GDRIVE_ARCHIVE` and Drive path `STELLCODEX/01_CANONICAL_CONTEXT/V10_MASTER_PACKAGE/`
- `docs/ops/evidence/*` -> GitHub-backed operational evidence under `02_GITHUB_CANON`
