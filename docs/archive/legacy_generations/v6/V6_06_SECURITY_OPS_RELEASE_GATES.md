## Archive Note

- Reason retired: This V6 security and release-gate pack was merged into the V10 security, operations, and release documents.
- Replaced by: `docs/v10/07_V10_SECURITY_LIMITS_AND_COMPLIANCE.md`, `docs/v10/10_V10_DEPLOY_BACKUP_RESTORE.md`, and `docs/v10/11_V10_RELEASE_GATES_AND_SMOKE.md`
- Historical value: Yes. It preserves the older release-gate framing.

# Security & Release Gate

Release şartları:
- Contract tests PASS
- Smoke gate PASS
- storage_key leak yok
- assembly_meta mevcut

Daily:
- DB dump
- Object mirror

Weekly:
- Restore test + smoke
