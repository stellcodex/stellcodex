# STELLCODEX V10 Share And Public Access Contract

- Document ID: `V10-08`
- Status: `Active Canonical`
- Parent authority: `docs/v10/00_V10_MASTER_CONSTITUTION.md`, `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- Related documents: `docs/v10/05_V10_API_CONTRACTS.md`, `docs/v10/06_V10_VIEWER_AND_UI_CONTRACT.md`, `docs/v10/19_V10_FRONTEND_SURFACE_CONTRACT.md`
- Last updated: `2026-03-16`
- Language: `English`
- Scope: `Public share tokens, expiry behavior, and share-facing surfaces`
- Replacement rule: `Share behavior changes must update backend routes, frontend routes, and this file together.`

This document is governed by `docs/v10/00_V10_MASTER_CONSTITUTION.md` and `docs/v10/01_V10_SOURCE_HIERARCHY.md`. If any lower-level file conflicts with these authorities, this file must be updated to comply.

## Share Token Rules

- token length must be at least `64` random characters
- public share routes must resolve through `/s/{token}` or the frontend viewer share route backed by the same token
- revoked shares must invalidate immediately
- expired shares must return `410`

## Public Access Rules

- public access may expose only the intended shared artifact surfaces
- public routes may not leak storage paths, tenant internals, or admin state
- rate limiting and audit logging are mandatory on public share resolution

## Canonical Repo Anchors

- backend share routes: `backend/app/api/v1/routes/share.py`
- frontend share pages: `frontend/src/app/(viewer)/share/[token]/page.tsx`, `frontend/src/app/s/[token]/page.tsx`
- frontend share API proxies: `frontend/src/app/api/share/`
