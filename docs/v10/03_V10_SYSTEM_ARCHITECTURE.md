# STELLCODEX V10 System Architecture

- Document ID: `V10-03`
- Status: `Active Canonical`
- Parent authority: `docs/v10/00_V10_MASTER_CONSTITUTION.md`, `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- Related documents: `docs/v10/04_V10_DATA_MODEL.md`, `docs/v10/10_V10_DEPLOY_BACKUP_RESTORE.md`, `docs/v10/15_V10_GITHUB_REPOSITORY_MAP.md`
- Last updated: `2026-03-23`
- Language: `English`
- Scope: `System domains, runtime components, and rebuildability rules`
- Replacement rule: `Architecture changes must be recorded here before they are treated as active truth anywhere else.`

This document is governed by `docs/v10/00_V10_MASTER_CONSTITUTION.md` and `docs/v10/01_V10_SOURCE_HIERARCHY.md`. If any lower-level file conflicts with these authorities, this file must be updated to comply.

## Fixed Domains

### Domain A: GitHub Canon

GitHub stores:
- source code
- infrastructure definitions
- migrations
- tests
- contracts
- scripts
- the active V10 documentation package

### Domain B: Google Drive Archive

Drive stores:
- backups
- restore proofs
- release evidence bundles
- reports
- exports
- frozen references
- continuation bundles

### Domain C: Disposable Runtime

The runtime is built from:
- containers and compose definitions
- environment templates
- GitHub code
- Drive backups and evidence

If the server disappears, the platform must be rebuildable from GitHub and Drive without hidden operator memory.

## Current Runtime Components

- `frontend/`: STELLCODEX product shell served on `127.0.0.1:3010` behind nginx
- `backend/`: API and persistence boundary served on `127.0.0.1:8000`
- `services/stell_ai/`: independent STELL.AI intelligence authority on the internal Docker network only
- `services/orchestra/`: independent Orchestra execution authority on the internal Docker network only
- `infrastructure/deploy/docker-compose.yml`: the single canonical runtime definition
- `infrastructure/nginx/stellcodex.conf`: the single canonical public edge definition
- `ops/` and `scripts/`: backup, cleanup, deploy, smoke, and evidence automation

## Zone Boundaries

- `STELLCODEX`: website, workspace, viewer, share surface, admin shell
- `STELL.AI`: planning, analysis, decision authority, memory write/search
- `Orchestra`: workflow state transitions, approvals, required inputs, share-readiness execution
- `backend`: public API, auth, tenancy checks, persistence, storage access, and service proxying

## Event And Processing Model

The platform uses queued worker execution for file processing and internal service calls for intelligence and workflow control.

The canonical chain is:
`upload -> worker processing -> STELL.AI decision -> Orchestra state sync -> approval/share progression`

No backend-owned state machine or backend-owned intelligence path is canonical after this revision.

## Architecture Rule

No hidden product surface, hidden storage domain, or server-only knowledge source is allowed.
Any long-lived operational memory must be exported into `docs/v10`, `STELLCODEX_ARCHIVE_ROOT`, or Drive.
