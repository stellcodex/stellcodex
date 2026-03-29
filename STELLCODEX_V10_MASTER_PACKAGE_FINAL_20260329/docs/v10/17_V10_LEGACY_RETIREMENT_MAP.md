# STELLCODEX V10 Legacy Retirement Map

- Document ID: `V10-17`
- Status: `Active Canonical`
- Parent authority: `docs/v10/00_V10_MASTER_CONSTITUTION.md`, `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- Related documents: `docs/manifests/LEGACY_RETIREMENT_MANIFEST.md`, `docs/indexes/LEGACY_INDEX.md`, `docs/archive/README.md`
- Last updated: `2026-03-23`
- Language: `English`
- Scope: `How legacy authority is isolated without destroying historical value`
- Replacement rule: `New legacy retirements must be recorded here and in the retirement manifest.`

This document is governed by `docs/v10/00_V10_MASTER_CONSTITUTION.md` and `docs/v10/01_V10_SOURCE_HIERARCHY.md`. If any lower-level file conflicts with these authorities, this file must be updated to comply.

## Retirement Rule

The following materials are never active authority after V10:
- old constitutions
- master prompts
- rebuild execution packs from older protocol generations
- frozen historical reports presented as if they were current plans

## Legacy Zones

- `docs/archive/legacy_generations/`: superseded V6 and V7 authority files
- `docs/archive/historical_protocols/`: retired execution protocols and plans
- `docs/archive/old_prompts/`: prompts and operator context files with historical value only
- `docs/archive/frozen_reports/`: dated evidence and historical reports
- retired runtime artifacts: `docker/docker-compose.prod.yml`, `ops/deploy/docker-compose.ghcr.yml`, `frontend/vercel.json`, `frontend__DISABLED__20260320_193121/`
- retired public contract: `/api/v1/auth/guest`

## Operator Rule

Legacy files may be read for context, but active work must be written back into `docs/v10/` or the archive manifests.
