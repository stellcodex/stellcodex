# STELLCODEX V10 Frontend Surface Contract

- Document ID: `V10-19`
- Status: `Active Canonical`
- Parent authority: `docs/v10/00_V10_MASTER_CONSTITUTION.md`, `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- Related documents: `docs/v10/06_V10_VIEWER_AND_UI_CONTRACT.md`, `docs/v10/08_V10_SHARE_AND_PUBLIC_ACCESS_CONTRACT.md`, `docs/v10/12_V10_OPERATIONS_AND_ADMIN.md`
- Last updated: `2026-03-28`
- Language: `English`
- Scope: `Canonical surface names, current route mapping, and hidden-surface prohibition`
- Replacement rule: `Surface changes must update this file before new routes are treated as active product surfaces.`

This document is governed by `docs/v10/00_V10_MASTER_CONSTITUTION.md` and `docs/v10/01_V10_SOURCE_HIERARCHY.md`. If any lower-level file conflicts with these authorities, this file must be updated to comply.

## Canonical Surface Names

Core product surfaces:
- Dashboard
- Projects
- Files
- Viewer
- Shares
- Admin
- Settings

Support surfaces:
- Root Redirect
- Auth
- Public Share

## Current Route Mapping

- Root redirect: `/` -> `/sign-in` or `/dashboard` depending on session state
- Auth: `/sign-in`
- Dashboard: `/dashboard`
- Projects: `/projects`, `/projects/[projectId]`
- Files: `/files/[fileId]`, `/files/[fileId]/viewer`, `/files/[fileId]/versions`
- Viewer: `/viewer?id={file_id}`
- Shares: `/shares`, `/s/[token]`, `/share/[token]`
- Settings: `/settings`
- Admin: `/admin`, `/admin/health`, `/admin/files`, `/admin/users`, `/admin/queues`, `/admin/queues/failed`, `/admin/audit`

## Surface Rule

No hidden surface is allowed.
Experimental routes may exist in code, but they are not product authority until they are named here.
