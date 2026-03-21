# STELLCODEX V10 Context Continuation Protocol

- Document ID: `V10-16`
- Status: `Active Canonical`
- Parent authority: `docs/v10/00_V10_MASTER_CONSTITUTION.md`, `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- Related documents: `docs/v10/13_V10_EXECUTION_ROADMAP.md`, `docs/v10/15_V10_GITHUB_REPOSITORY_MAP.md`, `STELLCODEX_ARCHIVE_ROOT/00_MASTER_INDEX/CONTINUATION_CONTEXT.md`
- Last updated: `2026-03-16`
- Language: `English`
- Scope: `One-file continuation state for future sessions`
- Replacement rule: `This file must stay current whenever canonical structure, restore status, or next actions materially change.`

This document is governed by `docs/v10/00_V10_MASTER_CONSTITUTION.md` and `docs/v10/01_V10_SOURCE_HIERARCHY.md`. If any lower-level file conflicts with these authorities, this file must be updated to comply.

## What STELLCODEX Is

STELLCODEX is a deterministic manufacturing decision platform with upload, processing, DFM, viewer, share, admin, and evidence capabilities.

## What Is Fixed

- GitHub is the active canonical source
- Google Drive is the long-term archive and evidence vault
- the server is disposable runtime only
- the V10 package under `docs/v10/` is the only active canonical doc set
- restore proof coverage currently passes across DB, object storage, worker, and API
- the live frontend cutover completed on `2026-03-16` against `https://stellcodex.com`
- the current live snapshot commit is `e0aa81f`
- the GitHub backup branch for the live cutover is `backup/20260316-live-frontend-cutover`

## Where Canonical Docs Are

- `docs/v10/00_V10_MASTER_CONSTITUTION.md`
- `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- `docs/indexes/MASTER_DOC_INDEX.md`

## Where Backups And Evidence Live

- local proofs: `evidence/`
- local backup artifacts: `backups/`
- Drive mirrors and archive manifests: `STELLCODEX_ARCHIVE_ROOT/03_GDRIVE_ARCHIVE/`
- continuity memory: `STELLCODEX_ARCHIVE_ROOT/00_MASTER_INDEX/`
- deploy rollback backup: `/var/www/stellcodex/_deploy_backups/frontend_20260316T171853Z.tgz`
- latest Drive DB dump after live cutover: `db_20260316_203205.sql.gz`

## What Must Not Be Rediscovered Again

- product identity and module boundaries
- GitHub vs Drive vs runtime separation
- source-of-truth order
- server disposability rule
- release and restore proof requirements

## Likely Next Execution Areas

- merge the live cutover backup branch into `main` through the protected-branch workflow
- update release automation so GitHub status checks close before protected-branch promotion
- inline archive hash normalization
- broader Drive inventory import
- route and terminology drift cleanup
- recurring logrotate observation

## Resume Rule

Start from this file, then read:
1. `docs/indexes/MASTER_DOC_INDEX.md`
2. `STELLCODEX_ARCHIVE_ROOT/00_MASTER_INDEX/CURRENT_STATE.md`
3. `docs/manifests/FINAL_CONSOLIDATION_REPORT.md`
