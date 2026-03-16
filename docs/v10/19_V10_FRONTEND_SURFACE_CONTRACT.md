# STELLCODEX V10 Frontend Surface Contract

- Document ID: `V10-19`
- Status: `Active Canonical`
- Parent authority: `docs/v10/00_V10_MASTER_CONSTITUTION.md`, `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- Related documents: `docs/v10/06_V10_VIEWER_AND_UI_CONTRACT.md`, `docs/v10/08_V10_SHARE_AND_PUBLIC_ACCESS_CONTRACT.md`, `docs/v10/12_V10_OPERATIONS_AND_ADMIN.md`
- Last updated: `2026-03-16`
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
- Home
- Features
- Docs
- Formats
- Community
- Auth
- Status

## Current Route Mapping

- Dashboard: `/dashboard`, `/dashboard/files`, `/dashboard/shares`, `/dashboard/settings`
- Projects and workspace: `/projects`, `/project/[id]`, `/workspace/[workspaceId]/[[...slug]]`
- Files and library: `/files`, `/library`
- Viewer: `/view`, `/viewer/[file_id]`, `/(viewer)/view/[scx_id]`
- Shares: `/share`, `/shares`, `/s/[token]`, `/(viewer)/share/[token]`
- Settings: `/settings`
- Admin: `/admin`, `/admin/health`, `/admin/files`, `/admin/shares`, `/admin/users`, `/admin/approvals`, `/admin/queue`, `/admin/rbac`, `/admin/system`, `/admin/ai`, `/admin/stell`, `/admin/audit`
- Public support: `/`, `/home`, `/features`, `/community`, `/docs`, `/formats`, `/pricing`, `/privacy`, `/terms`, `/status`, `/login`, `/register`, `/forgot`, `/reset`, `/reset-password`, `/upload`

## Surface Rule

No hidden surface is allowed.
Experimental routes may exist in code, but they are not product authority until they are named here.
