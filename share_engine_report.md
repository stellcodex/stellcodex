# Share Engine Report (V7 Audit)

Audit timestamp: 2026-03-08 (UTC)
Evidence bundle: `/root/workspace/evidence/v7_fix_run_20260308T032241Z`

## Contract checks
Verified endpoints:
- `POST /api/v1/shares`
- `GET /s/{token}`
- revoke endpoint

Runtime checks:
- token length >= 64 (observed: 64)
- expiry required in API schema
- expired share returns HTTP 410
- revoke invalidates immediately
- rate limit enforced

Evidence:
- `smoke/share_create.json`
- `smoke/share_expired_410.json`
- `smoke/share_revoke_denied.json`
- `smoke/summary.json`
- OpenAPI required fields include `expires_in_seconds` for `ShareCreateIn` and `ShareCreateAliasIn`.

## Section verdict
PASS
