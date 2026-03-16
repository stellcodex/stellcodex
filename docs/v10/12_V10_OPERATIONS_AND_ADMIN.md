# STELLCODEX V10 Operations And Admin

- Document ID: `V10-12`
- Status: `Active Canonical`
- Parent authority: `docs/v10/00_V10_MASTER_CONSTITUTION.md`, `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- Related documents: `docs/v10/07_V10_SECURITY_LIMITS_AND_COMPLIANCE.md`, `docs/v10/11_V10_RELEASE_GATES_AND_SMOKE.md`, `docs/v10/19_V10_FRONTEND_SURFACE_CONTRACT.md`
- Last updated: `2026-03-16`
- Language: `English`
- Scope: `Admin surfaces, operator actions, and operational limits`
- Replacement rule: `Admin or operator workflow changes must update this document and the frontend surface contract together.`

This document is governed by `docs/v10/00_V10_MASTER_CONSTITUTION.md` and `docs/v10/01_V10_SOURCE_HIERARCHY.md`. If any lower-level file conflicts with these authorities, this file must be updated to comply.

## Admin Scope

The admin domain covers:
- health and system status
- files and storage hygiene
- shares and public access control
- users and RBAC
- approvals
- queues and worker visibility
- audit visibility
- AI and STELL operator surfaces

## Critical Operations

The following actions require approvals, audit evidence, or both:
- destructive file actions
- restore drills
- queue pauses or restarts
- RBAC changes
- security policy changes

## Repo Anchors

- frontend admin routes: `frontend/src/app/(app)/admin/`
- backend admin routes: `backend/app/api/v1/routes/admin.py`
- RBAC policy: `security/rbac.policy.json`
- generated permissions: `frontend/src/security/`, `backend/app/security/`
