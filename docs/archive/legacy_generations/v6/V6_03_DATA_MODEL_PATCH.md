## Archive Note

- Reason retired: This V6 data model patch was absorbed into the V10 data model contract.
- Replaced by: `docs/v10/04_V10_DATA_MODEL.md`
- Historical value: Yes. It captures earlier data-model corrections.

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
