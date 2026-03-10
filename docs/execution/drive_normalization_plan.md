# Google Drive Normalization Plan

Updated: 2026-03-08 (UTC)

## Canonical Root (required)

```text
STELL/
  00_ARCHIVE
  01_BACKUPS
  02_DATASETS
  03_EVIDENCE
  04_REPORTS
  05_MODEL_OUTPUTS
  06_COMPANY_DOCS
  07_EXPORTS
  08_STELL_AI_MEMORY
  09_STELLCODEX_ARTIFACTS
  10_ORCHESTRA_JOBS
```

## Category Ownership
- `08_STELL_AI_MEMORY`: STELL.AI memory records, founder knowledge, solved cases, retrieval context snapshots.
- `10_ORCHESTRA_JOBS`: queue payload snapshots, worker outputs, ingestion/eval exports, retry/DLQ traces.
- `09_STELLCODEX_ARTIFACTS`: SCX bundles, DFM reports, quotes, share evidence, product artifacts.
- `03_EVIDENCE` + `04_REPORTS`: cross-system release proof and operational reporting.
- `01_BACKUPS`: permanent DB/object backup exports.

## Duplicate and Misplacement Policy
- Duplicate detection fingerprint: `checksum + size_bytes`.
- First canonical item stays in target folder; duplicates move to `00_ARCHIVE` with reason `duplicate_checksum_and_size`.
- Non-canonical placement must be moved to the canonical target path.

## Implemented Tooling
- Script: `/root/workspace/scripts/drive_normalize_manifest.py`
- Input formats: `.jsonl` or `.csv` inventory exports.
- Output: JSON manifest with action list (`move`, `keep`, `archive_duplicate`) and category summary.

### Example
```bash
./scripts/drive_normalize_manifest.py \
  --inventory drive_inventory.jsonl \
  --output docs/execution/drive_migration_manifest.json
```

## Execution Status
- Canonical structure, ownership, and migration algorithm: completed.
- Manifest generation tooling smoke test: completed.
- Live migration execution on `gdrive:`: completed.
  - Root normalized to a single canonical root (`gdrive:` now contains only `STELL`).
  - Canonical folders `00..10` verified under `STELL/`.
  - Migration evidence logs:
    - `/root/workspace/evidence/drive_normalize_20260308T004915Z.jsonl`
    - `/root/workspace/evidence/drive_normalize_20260308T005413Z.jsonl`
    - `/root/workspace/evidence/drive_normalize_root_apply_20260308T010510Z.jsonl`
    - `/root/workspace/evidence/drive_normalize_canonicalize_20260308T010903Z.jsonl`
    - `/root/workspace/evidence/drive_normalize_finalize_20260308T012859Z.jsonl`
- Quota-safe residual handling: completed.
  - Legacy residual buckets were relocated from `STELL/00_ARCHIVE/legacy_residuals` into ownership-aligned `_residual_imports` paths:
    - `STELL/06_COMPANY_DOCS/system_core/_residual_imports`
    - `STELL/01_BACKUPS/legacy_stellcodex-backups/_residual_imports`
    - `STELL/09_STELLCODEX_ARTIFACTS/stellcodex-genois/_residual_imports`
  - Relocation proof: `/root/workspace/evidence/drive_residual_relocation_status_20260308T0513Z.txt`
- Archive naming hardening: completed.
  - Timestamped folder `STELL/00_ARCHIVE/stellcodex-archive_20260308T010510Z` moved under canonical legacy archive imports:
    - `STELL/00_ARCHIVE/legacy_stellcodex-archive/_imports/stellcodex-archive_20260308T010510Z`
  - Updated archive layout proof: `/root/workspace/evidence/drive_archive_layout_status_20260308T0519Z.txt`
