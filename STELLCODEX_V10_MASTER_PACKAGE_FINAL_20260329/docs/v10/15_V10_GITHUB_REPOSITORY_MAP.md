# STELLCODEX V10 GitHub Repository Map

- Document ID: `V10-15`
- Status: `Active Canonical`
- Parent authority: `docs/v10/00_V10_MASTER_CONSTITUTION.md`, `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- Related documents: `docs/v10/03_V10_SYSTEM_ARCHITECTURE.md`, `docs/v10/10_V10_DEPLOY_BACKUP_RESTORE.md`, `docs/indexes/REPO_INDEX.md`
- Last updated: `2026-03-29`
- Language: `English`
- Scope: `Beginner-safe explanation of where code, docs, infra, evidence, and runtime assets live`
- Replacement rule: `Repository map changes must be updated here before new operators are expected to rely on them.`

This document is governed by `docs/v10/00_V10_MASTER_CONSTITUTION.md` and `docs/v10/01_V10_SOURCE_HIERARCHY.md`. If any lower-level file conflicts with these authorities, this file must be updated to comply.

In this workspace, split runtime repos are staged under `_canonical_repos/`. Production deploy roots are `/srv/stellcodex`, `/srv/stell-ai`, `/srv/orchestra`, and `/srv/infra`.

## Where Code Lives

- `backend/`: FastAPI API shell, persistence layer, workers, models, service clients, API routes, alembic migrations
- `frontend/`: Next.js STELLCODEX product shell, viewer pages, admin shell, route guards
- `_canonical_repos/stell-ai/`: standalone STELL.AI runtime owned by the canonical split repo
- `_canonical_repos/orchestra/`: standalone Orchestra runtime owned by the canonical split repo
- `db/`: SQL migration floor and migration references

## Where Infrastructure Lives

- `_canonical_repos/infra/`: canonical compose, nginx, runtime env contract, compliance helpers, and runtime ops
- `ops/`: workspace-local utility layer retained for backup-state, cron, and hygiene support

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
- alternate deploy definitions outside `_canonical_repos/infra/deploy/docker-compose.yml`
