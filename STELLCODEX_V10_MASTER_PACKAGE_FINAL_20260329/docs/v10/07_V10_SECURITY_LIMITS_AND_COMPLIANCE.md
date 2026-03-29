# STELLCODEX V10 Security Limits And Compliance

- Document ID: `V10-07`
- Status: `Active Canonical`
- Parent authority: `docs/v10/00_V10_MASTER_CONSTITUTION.md`, `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- Related documents: `docs/v10/05_V10_API_CONTRACTS.md`, `docs/v10/08_V10_SHARE_AND_PUBLIC_ACCESS_CONTRACT.md`, `docs/v10/12_V10_OPERATIONS_AND_ADMIN.md`
- Last updated: `2026-03-16`
- Language: `English`
- Scope: `Security boundaries, approval rules, and compliance expectations`
- Replacement rule: `Security boundary changes must be reflected here before release or operator rollout.`

This document is governed by `docs/v10/00_V10_MASTER_CONSTITUTION.md` and `docs/v10/01_V10_SOURCE_HIERARCHY.md`. If any lower-level file conflicts with these authorities, this file must be updated to comply.

## Locked Security Rules

- no `storage_key` leaks in public responses
- no client-supplied permissions
- critical operations require allowlisted tools and approval paths
- audit events are append-only
- secrets must be masked in logs and evidence bundles

## Rate Limit And Audit Rules

Minimum rate limits:
- auth: `10 req / 60s / IP`
- upload: `20 req / 60s / user`
- share resolve: `30 req / 60s / IP`

When exceeded:
- return `429`
- emit a `RATE_LIMIT` audit event
- record scope, identifier, limit, and window metadata

## Compliance Handling

- tenant isolation is mandatory
- archived evidence must preserve traceability without exposing secrets
- admin routes must be protected by RBAC and logged approvals where required
- runtime operators may not bypass GitHub-first change control
