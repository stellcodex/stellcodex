# Boundary Correction Report

Updated: 2026-03-08 (UTC)

## Confusion Detected
- Legacy `product` API contract exposed `revision_id` as public request input.
- Boundary documentation existed but execution evidence and ownership links were not tied to a passing release gate.
- Storage backup flow depended on external mirror variables only, blocking local immutable backup/restore proof.

## Corrections Implemented
- Enforced `file_id`-only public identity in product render/status contracts:
  - `stellcodex_v7/backend/app/api/v1/routes/product.py`
  - Replaced `RenderRequest.revision_id` with `RenderRequest.file_id`.
  - Added access checks aligned with tenant/user ownership for `/status/{file_id}` and `/render`.
- Removed legacy presigned artifact URL emission in product status response to prevent indirect internal key exposure.
- Hardened public leak protection in tests:
  - `stellcodex_v7/backend/tests/test_public_contract_leaks.py`
  - Added OpenAPI assertions to block `revision_id` and `storage_key`.
- Fixed orchestrator approval regression:
  - `stellcodex_v7/backend/app/core/orchestrator.py`
  - Manual approval (`approve_manual` / `approval_override=approved`) now preserves S7 instead of being auto-downgraded to S5 for missing optional inputs.
  - Added regression coverage in `stellcodex_v7/backend/tests/test_orchestrator_core.py`.
- Fixed storage mirror path for gate reliability:
  - `stellcodex_v7/infrastructure/deploy/scripts/backup_storage.sh`
  - Added local MinIO mirror fallback using `docker cp` when `RCLONE_STORAGE_SOURCE` / `S3_BUCKET` are not configured.
- Added operational boundary/split tooling:
  - `/root/workspace/scripts/verify_boundary_layout.sh`
  - `/root/workspace/scripts/prepare_repo_split.sh`
- Executed live Google Drive normalization on `gdrive:`:
  - Canonical root enforced as `STELL/00..10`.
  - Drive root normalized to single folder (`STELL`).
  - Residual/duplicate-heavy segments relocated into ownership-scoped `_residual_imports` paths under backups/docs/artifacts.
  - `00_ARCHIVE` timestamp spillover normalized into canonical legacy import path:
    - `STELL/00_ARCHIVE/legacy_stellcodex-archive/_imports/stellcodex-archive_20260308T010510Z`
  - Evidence logs:
    - `/root/workspace/evidence/drive_normalize_20260308T004915Z.jsonl`
    - `/root/workspace/evidence/drive_normalize_20260308T005413Z.jsonl`
    - `/root/workspace/evidence/drive_normalize_root_apply_20260308T010510Z.jsonl`
    - `/root/workspace/evidence/drive_normalize_canonicalize_20260308T010903Z.jsonl`
    - `/root/workspace/evidence/drive_normalize_finalize_20260308T012859Z.jsonl`
    - `/root/workspace/evidence/drive_residual_relocation_status_20260308T0513Z.txt`
    - `/root/workspace/evidence/drive_archive_layout_status_20260308T0519Z.txt`
- Enabled main branch protection on all boundary repositories with required checks and admin enforcement:
  - `stellcodex`: `backend-contracts`, `frontend-release-gate`
  - `stell-ai`: `verify-boundary-layout`
  - `orchestra`: `verify-boundary-layout`
  - `infra`: `verify-boundary-layout`
  - evidence: `/root/workspace/evidence/github_branch_protection_status_20260308T0525Z.txt`

## Verification
- Full V7 release gate passed end-to-end:
  - `/root/workspace/evidence/v7_gate_20260308T014732Z/gate_status.txt` = `PASS`
  - `/root/workspace/evidence/v7_gate_20260308T014732Z/restore_status.txt` = `PASS`
  - `/root/workspace/evidence/v7_gate_20260308T014732Z/smoke/smoke_test_status.txt` = `PASS`

## Remaining External Normalization Work
- No remaining release-blocking external normalization work.
