# STELLCODEX V10 System Architecture

- Document ID: `V10-03`
- Status: `Active Canonical`
- Parent authority: `docs/v10/00_V10_MASTER_CONSTITUTION.md`, `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- Related documents: `docs/v10/04_V10_DATA_MODEL.md`, `docs/v10/10_V10_DEPLOY_BACKUP_RESTORE.md`, `docs/v10/15_V10_GITHUB_REPOSITORY_MAP.md`
- Last updated: `2026-03-16`
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

- `backend/` FastAPI application and workers
- `frontend/` Next.js application
- `db/` SQL migrations
- `docker/` and `infrastructure/` runtime topology
- `ops/` operational automation
- `scripts/` release, smoke, backup, and restore proof scripts

## Event And Processing Model

The platform uses queued and event-like processing around Redis, worker tasks, and state transitions.
CloudEvents-compatible metadata is the target event contract for cross-service communication.

The deterministic chain is:
`upload -> convert -> assembly_meta -> rule_engine -> dfm_engine -> report -> pack -> archive`

## Architecture Rule

No hidden product surface, hidden storage domain, or server-only knowledge source is allowed.
Any long-lived operational memory must be exported into `docs/v10`, `STELLCODEX_ARCHIVE_ROOT`, or Drive.
