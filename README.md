# STELLCODEX — Ultra Production-Ready Baseline (V7)

Generated: 2026-02-27 02:01:13 UTC

This bundle is a production-grade skeleton that enforces V7 as the *single* binding constitution and provides:
- Docker production stack (nginx + backend + worker + postgres + redis + minio)
- Example env templates (safe)
- GitHub Actions CI workflow with contract + leak + smoke + schema validation
- Contract test matrix scripts
- storage_key leak test (runtime + repo scan)
- decision_json schema validator
- rate-limit & audit event spec
- DB migration templates for orchestrator_sessions + rule_configs
- Backup/restore automation + weekly restore gate
- Release gate script that blocks deploy if anything fails

Canonical constitution:
docs/constitution/STELLCODEX_V7_MASTER.md

redeploy trigger
