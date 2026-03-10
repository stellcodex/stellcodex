# Provider Audit Scope Guide

This guide lists minimum token scopes/permissions for read-only live audit.

## Cloudflare

- Token type: API Token (not Global API Key).
- Recommended account/zone scope:
  - `Account.Workers Scripts:Read`
  - `Zone.DNS:Read`
  - `Zone.Workers Routes:Read`
  - `Account.Account Settings:Read` (or equivalent account listing read scope)
- Resource scope:
  - Restrict to STELL account and `stellcodex.com` zone only.

## Vercel

- Token type: Personal or Team token with read-only project access.
- Recommended permissions:
  - Projects: Read
  - Deployments: Read
  - Environment Variables: Read metadata (non-decrypt mode is used by audit script)
- Scope:
  - Restrict to STELL team/org and STELL projects.

## Notes

- Audit scripts do not print secret values.
- `provider_live_audit.sh` queries public provider APIs with bearer auth and stores only counts/status metadata.
- Recommended location:
  - `/root/workspace/.secrets/provider_audit.env` with permissions `chmod 600`
- Fallback locations:
  - `/root/workspace/.env`
  - `/root/stell/.env`
  - `/root/stell/webhook/.env`
