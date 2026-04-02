# STELLCODEX V10 System Architecture

- Document ID: `V10-03`
- Status: `Active Canonical`
- Parent authority: `docs/v10/00_V10_MASTER_CONSTITUTION.md`, `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- Related documents: `docs/v10/04_V10_DATA_MODEL.md`, `docs/v10/10_V10_DEPLOY_BACKUP_RESTORE.md`, `docs/v10/15_V10_GITHUB_REPOSITORY_MAP.md`
- Last updated: `2026-04-02`
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
- `_canonical_repos/stell-ai/`: canonical STELL.AI split-runtime target location used when the split repo is staged in this workspace and deployed from `/srv/stell-ai`
- `_canonical_repos/orchestra/`: canonical Orchestra split-runtime target location used when the split repo is staged in this workspace and deployed from `/srv/orchestra`
- `_canonical_repos/infra/deploy/docker-compose.yml`: the single canonical runtime definition
- `_canonical_repos/infra/nginx/stellcodex.conf`: the single canonical public edge definition
- `_canonical_repos/infra/ops/` and `scripts/`: backup, cleanup, deploy, smoke, and evidence automation

Within this workspace, split runtime repos are staged under `_canonical_repos/` when present. Production targets the corresponding runtime under `/srv/stellcodex`, `/srv/stell-ai`, `/srv/orchestra`, and `/srv/infra`.

## Verified Runtime Posture

Current verified repository reality is a hybrid proxy-gated split architecture.

STELL-AI request handling is proxied through backend integration surfaces. Backend remains the auth, tenancy, persistence, request validation, service proxy, and admin observability boundary in the current verified repository state.

The V10 split-runtime model remains the active direction, but full split-closure is an architectural target and not a blanket execution fact for every surface in the current repository state.

Documented split-runtime targets must remain aligned with physically verifiable repository state.

## Zone Boundaries

- `STELLCODEX`: website, workspace, viewer, share surface, admin shell
- `STELL.AI`: planning, analysis, decision authority, memory write/search
- `Orchestra`: workflow state transitions, approvals, required inputs, share-readiness execution
- `backend`: public API, auth, tenancy checks, persistence, storage access, service proxying, and admin observability surfaces

## Event And Processing Model

The platform uses queued worker execution for file processing and internal service calls for intelligence and workflow control.

The canonical chain is:
`upload -> worker processing -> STELL.AI memory retrieval and decision -> Orchestra state sync and case logging -> approval/share progression`

Current execution remains proxy-gated through backend integration boundaries while split authorities are enforced incrementally across dedicated runtimes.

## Architecture Rule

No hidden product surface, hidden storage domain, or server-only knowledge source is allowed.
Any long-lived operational memory must be exported into `docs/v10`, `STELLCODEX_ARCHIVE_ROOT`, or Drive.
