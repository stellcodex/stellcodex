# Data Model Policy (V7)

Required tables:
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
- orchestrator_sessions (decision_json NOT NULL)
- rule_configs (threshold store)

Hardcoded thresholds are forbidden.
