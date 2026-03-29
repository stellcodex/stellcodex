# STELLCODEX V10 Deploy Backup Restore

- Document ID: `V10-10`
- Status: `Active Canonical`
- Parent authority: `docs/v10/00_V10_MASTER_CONSTITUTION.md`, `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- Related documents: `docs/v10/03_V10_SYSTEM_ARCHITECTURE.md`, `docs/v10/11_V10_RELEASE_GATES_AND_SMOKE.md`, `docs/v10/14_V10_DRIVE_ARCHIVE_HIERARCHY.md`
- Last updated: `2026-03-29`
- Language: `English`
- Scope: `Deploy discipline, backup sources, restore proof, and disposability rules`
- Replacement rule: `Deploy or restore process changes must update this file and the evidence standard before use.`

This document is governed by `docs/v10/00_V10_MASTER_CONSTITUTION.md` and `docs/v10/01_V10_SOURCE_HIERARCHY.md`. If any lower-level file conflicts with these authorities, this file must be updated to comply.

## Deploy Rules

- no hot patching in production
- repo change -> build -> recreate -> verify -> archive evidence
- runtime must be reconstructable from GitHub code, Drive backups, and environment templates

## Canonical Automation

- deploy topology: `_canonical_repos/infra/deploy/docker-compose.yml`
- edge topology: `_canonical_repos/infra/nginx/stellcodex.conf`, `_canonical_repos/infra/nginx/cloudflare-real-ip.conf`
- runtime env file: `/srv/infra/runtime/infra.deploy.env`
- backup scripts: `scripts/backup_db.sh`, `scripts/backup_object_mirror.sh`, `_canonical_repos/infra/ops/scripts/backup-state.sh`
- restore proof scripts: `scripts/weekly_restore_gate.sh`, `scripts/object_restore_drill.sh`, `scripts/runtime_restore_probe.sh`
- cleanup automation: `_canonical_repos/infra/ops/scripts/cleanup.sh`, `_canonical_repos/infra/ops/scripts/install_cleanup_cron.sh`

Alternative compose files and side-port deploy paths are retired.

## Restore Guarantee

The restore program must prove:
- database recovery
- object storage recovery
- worker recovery
- API recovery

Restore without evidence is invalid.

## Runtime Storage Rule

The server may cache runtime artifacts temporarily, but it may not be the only copy of any critical backup, proof, or context asset.
