# Evidence Pack

Updated: 2026-03-08 (UTC)

## Primary Evidence Bundle
- `/root/workspace/evidence/v7_gate_20260308T014732Z`

## PASS Markers
- Gate: `/root/workspace/evidence/v7_gate_20260308T014732Z/gate_status.txt`
- Restore: `/root/workspace/evidence/v7_gate_20260308T014732Z/restore_status.txt`
- Smoke: `/root/workspace/evidence/v7_gate_20260308T014732Z/smoke/smoke_test_status.txt`

## Core Runtime Proof Files
- Schema validation: `/root/workspace/evidence/v7_gate_20260308T014732Z/db_schema_check.txt`
- Contract suite log: `/root/workspace/evidence/v7_gate_20260308T014732Z/contract_tests.log`
- Leak check log: `/root/workspace/evidence/v7_gate_20260308T014732Z/leak_check.txt`
- Restore run log: `/root/workspace/evidence/v7_gate_20260308T014732Z/restore.txt`
- Gate run log: `/root/workspace/evidence/v7_gate_20260308T014732Z/release_gate.log`
- Full backend tests: `/root/workspace/evidence/backend_pytest_full_20260308T0156Z.txt`

## Backup / Integrity Proof Files
- DB dump: `/root/workspace/evidence/v7_gate_20260308T014732Z/backups/postgres_20260308T014954Z.dump`
- DB hash: `/root/workspace/evidence/v7_gate_20260308T014732Z/backups/postgres_20260308T014954Z.sha256`
- Storage mirror manifest: `/root/workspace/evidence/v7_gate_20260308T014732Z/backups/storage_20260308T014958Z/object_manifest.sha256`

## Live Drive Normalization Proof Files
- `/root/workspace/evidence/drive_normalize_20260308T004915Z.jsonl` (dry-run planning log)
- `/root/workspace/evidence/drive_normalize_20260308T005413Z.jsonl` (initial apply log)
- `/root/workspace/evidence/drive_normalize_root_apply_20260308T010510Z.jsonl` (root-level canonical move log)
- `/root/workspace/evidence/drive_normalize_canonicalize_20260308T010903Z.jsonl` (category canonicalization log)
- `/root/workspace/evidence/drive_normalize_finalize_20260308T012859Z.jsonl` (finalization log)
- `/root/workspace/evidence/size_src_02_backups.json`
- `/root/workspace/evidence/size_dst_02_backups.json`
- `/root/workspace/evidence/drive_root_stellcodex_residual_ts.txt`
- `/root/workspace/evidence/drive_root_canonical_status_20260308T0143Z.txt`
- `/root/workspace/evidence/drive_residual_relocation_status_20260308T0513Z.txt`
- `/root/workspace/evidence/drive_archive_layout_status_20260308T0519Z.txt`

## GitHub Split / CI Proof Files
- `/root/workspace/evidence/github_split_status_20260308T0524Z.txt`
- `/root/workspace/evidence/repo_remote_split_base.txt`
- `/root/workspace/evidence/github_branch_protection_status_20260308T0525Z.txt`

## Code Changes (this execution)
- `stellcodex_v7/backend/app/api/v1/routes/product.py`
- `stellcodex_v7/backend/app/core/orchestrator.py`
- `stellcodex_v7/backend/tests/test_orchestrator_core.py`
- `stellcodex_v7/backend/tests/test_public_contract_leaks.py`
- `stellcodex_v7/infrastructure/deploy/scripts/backup_storage.sh`
- `scripts/drive_normalize_manifest.py`
- `scripts/drive_normalize_apply.sh`
- `scripts/verify_boundary_layout.sh`
- `scripts/prepare_repo_split.sh`
- `docs/execution/*.md` (A-F report refresh)

## Verification Commands Run
- `cd /root/workspace/stellcodex_v7/backend && pytest -q`
- `cd /root/workspace/stellcodex_v7/backend && python3 -m compileall -q app tests`
- `/root/workspace/stellcodex_v7/infrastructure/deploy/scripts/release_gate_v7.sh`
- `/root/workspace/scripts/drive_normalize_manifest.py --inventory <sample.jsonl> --output <manifest.json>`
- `rclone lsd gdrive:`
- `rclone lsd gdrive:STELL`
- `gh repo view stellcodex/{stell-ai,orchestra,stellcodex,infra}`
- `gh run list -R stellcodex/<repo> --limit 1`
- `gh api repos/stellcodex/stellcodex/branches/main/protection`
- `/root/workspace/scripts/verify_boundary_layout.sh`
- `/root/workspace/scripts/prepare_repo_split.sh`

## Additional Outputs
- Boundary layout verification: `PASS all-boundaries`
- Repo split bundle: `/root/workspace/_runs/repo_split_20260308T015347Z`
