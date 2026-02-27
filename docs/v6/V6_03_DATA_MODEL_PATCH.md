# Data Model Patch

Zorunlu tablolar:
- files
- orchestrator_sessions
- shares
- audit_events
- rule_configs

orchestrator_sessions:
- file_id
- state
- decision_json (NOT NULL)
- rule_version
- mode
- confidence
