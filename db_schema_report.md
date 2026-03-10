# DB Schema Report (V7 Audit)

Audit timestamp: 2026-03-08 (UTC)
Evidence: `/root/workspace/evidence/v7_fix_run_20260308T032241Z/db_schema_check.txt`

## Required tables
Present:
- users
- tenants
- memberships
- plans
- subscriptions
- projects
- files
- file_versions
- jobs
- job_logs
- shares
- audit_events
- orchestrator_sessions
- rule_configs

## Critical checks
- `orchestrator_sessions.decision_json` NOT NULL: PASS (`missing_orchestrator_decision_json=0`)
- `rule_configs` exists and loaded: PASS (17 enabled keys)
- `uploaded_files.tenant_id` exists and NOT NULL: PASS (`missing_tenant_id=0`)
- V7 fields check in schema gate: PASS (`missing_v7_fields=0`)

## Section verdict
PASS
