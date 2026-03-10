# STELLCODEX Prefight Audit

- generated_at: 2026-03-10T10:17:41.597259Z
- repository_branch: master
- backend_health_http: 200
- orchestrator_health_http: 200
- schema_check: PASS
- contract_tests: PASS
- smoke_pipeline: PASS after repo remediation
- backup_restore: PASS

## Findings
- BLOCKER `BLOCKER-COMPOSE-EXEC-HANG`: deploy automation scripts hung on compose exec paths; resolved in repo by `compose_exec` remediation.
- BLOCKER `BLOCKER-AI-PYTHON38-COMPAT`: host default Python 3.8 could not satisfy the requested AI stack; resolved by installing Python 3.9 and rebuilding `AI/.venv`.
- MAJOR `MAJOR-DIRTY-WORKTREE`: git sync apply remains skipped on the live tree because unrelated local changes exist; final runtime proof will use a clean commit snapshot.

## Evidence
- schema: /root/workspace/evidence/preflight_schema_20260310T091237Z/db_schema_check.txt
- contracts: /root/workspace/evidence/preflight_contracts_20260310T091237Z/contract_tests.log
- smoke: /root/workspace/evidence/preflight_smoke_execfix_20260310T092348Z/smoke
- leak_check: /root/workspace/evidence/preflight_smoke_execfix_20260310T092348Z/leak_check.txt
- backup: /root/workspace/evidence/preflight_backup_20260310T092634Z/backups/backup_20260310T092634Z.txt
- restore: /root/workspace/evidence/preflight_backup_20260310T092634Z/restore_verify.txt
- git_sync: /root/workspace/_jobs/reports/stellcodex_git_sync_latest.json
