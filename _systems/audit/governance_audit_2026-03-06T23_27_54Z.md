# Governance Audit

Generated: 2026-03-06T23:27:54Z

## Manifest Presence
- STELL manifest: PASS
  detail: /root/workspace/_systems/STELL_CORE/ACTIVE_STELL_MANIFEST.json
- ORCHESTRA manifest: PASS
  detail: /root/workspace/_systems/ORCHESTRA_CORE/ACTIVE_ORCHESTRA_MANIFEST.json
- STELLCODEX manifest: PASS
  detail: /root/workspace/_systems/STELLCODEX_CORE/ACTIVE_STELLCODEX_MANIFEST.json
- INTEGRATION manifest: PASS
  detail: /root/workspace/_systems/INTEGRATION_CORE/ACTIVE_INTEGRATION_MANIFEST.json
- INFRA manifest: PASS
  detail: /root/workspace/_systems/INFRA_CORE/INFRA_CONNECTION_MANIFEST.json

## Guardrails
- duplicate_prompt_detection: FAIL
  detail: duplicate filenames: STELLCODEX_MASTER_PROMPT_v8.0.md
- manifest_authority_violation: PASS
  detail: integration manifest contains allowed flow boundary and audit trigger
- secret_exposure_detection: PASS
  detail: secret report present; findings indexed: 98
- backup_verification_failure: PASS
  detail: backups found: 20; latest: /root/stellcodex_output/backups/backup_20260306_223229.zip
- external_connector_health_failure: PASS
  detail: github origin and redis queue connector healthy

## Summary
- pass: 9
- fail: 1
