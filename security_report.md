# Security Report (V7 Audit)

Audit timestamp: 2026-03-08 (UTC)
Evidence bundle: `/root/workspace/evidence/v7_fix_run_20260308T032241Z`

## Verified controls
- MIME sniffing + extension guard active on upload.
- Virus scan stage present in worker pipeline.
- Upload/share/token-probe rate limiting enforced.
- Audit events generated for share + approval actions.
- Public key leak checks pass.

## Tenant isolation
Explicit model verified:
- `uploaded_files.tenant_id` exists and NOT NULL.
- storage object paths are tenant-scoped (`uploads/tenant_<id>/...`).

Runtime DB checks:
- `tenant_id IS NULL` rows: `0`
- tenant-scoped upload path rows: present

## Section verdict
PASS
