# STELLCODEX V10 GitHub Repository Map

- Document ID: `V10-15`
- Status: `Active Canonical`
- Parent authority: `docs/v10/00_V10_MASTER_CONSTITUTION.md`, `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- Related documents: `docs/v10/03_V10_SYSTEM_ARCHITECTURE.md`, `docs/v10/10_V10_DEPLOY_BACKUP_RESTORE.md`, `docs/indexes/REPO_INDEX.md`
- Last updated: `2026-03-16`
- Language: `English`
- Scope: `Beginner-safe explanation of where code, docs, infra, evidence, and runtime assets live`
- Replacement rule: `Repository map changes must be updated here before new operators are expected to rely on them.`

This document is governed by `docs/v10/00_V10_MASTER_CONSTITUTION.md` and `docs/v10/01_V10_SOURCE_HIERARCHY.md`. If any lower-level file conflicts with these authorities, this file must be updated to comply.

## Where Code Lives

- `backend/`: FastAPI app, workers, models, services, API routes, alembic migrations
- `frontend/`: Next.js app, UI routes, viewer pages, frontend security and route guards
- `db/`: SQL migration floor and migration references

## Where Infrastructure Lives

- `docker/`: production compose and nginx assets
- `infrastructure/`: deploy stack, runtime compose, nginx, compliance helpers
- `ops/`: cleanup, backup-state, cron, logrotate, runtime hygiene

## Where Active Docs Live

- `docs/v10/`: the only active canonical documentation set
- `docs/indexes/`: operator indexes into canonical docs and archive maps
- `docs/manifests/`: migration, retirement, authority, and consolidation manifests

## Where Supporting And Historical Docs Live

- `docs/contracts/`, `docs/data_model/`, `docs/security/`, `docs/compatibility/`: supporting input documents
- `docs/archive/`: historical references, old prompts, frozen reports, superseded generations
- `STELLCODEX_ARCHIVE_ROOT/`: archive continuity and mirror manifests

## Where Runtime Proof Lives

- `scripts/`: release, smoke, backup, and restore proof automation
- `evidence/`: local runtime proof outputs
- `backups/`: local backup artifacts before Drive mirror

## What Must Never Become Long-Term Truth

- ad hoc files on the server
- container writable layers
- untracked operator notes
- prompt text that is not absorbed into `docs/v10/`
