# Governance Guardrail Checks

Mandatory automated checks:

1. duplicate_prompt_detection
2. manifest_authority_violation
3. secret_exposure_detection
4. backup_verification_failure
5. external_connector_health_failure

Trigger rule:
Any failed check must append an entry under `_systems/audit/final_system_state.md` and produce a timestamped audit note.
