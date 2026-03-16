# STELLCODEX V10 Source Hierarchy

- Document ID: `V10-01`
- Status: `Active Canonical`
- Parent authority: `docs/v10/00_V10_MASTER_CONSTITUTION.md`
- Related documents: `docs/v10/14_V10_DRIVE_ARCHIVE_HIERARCHY.md`, `docs/v10/15_V10_GITHUB_REPOSITORY_MAP.md`, `docs/manifests/FILE_AUTHORITY_MAP.md`
- Last updated: `2026-03-16`
- Language: `English`
- Scope: `Authority resolution, repository truth handling, and archive separation`
- Replacement rule: `If hierarchy rules change, this file must be updated before any lower-level document or operational procedure is changed.`

This document is governed by `docs/v10/00_V10_MASTER_CONSTITUTION.md`. If any lower-level file conflicts with this hierarchy, that file must be updated or retired.

## Active Canonical Set

The only active canonical documentation set is:
- `docs/v10/00_V10_MASTER_CONSTITUTION.md`
- `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- `docs/v10/02_V10_PRODUCT_SCOPE_AND_IDENTITY.md`
- `docs/v10/03_V10_SYSTEM_ARCHITECTURE.md`
- `docs/v10/04_V10_DATA_MODEL.md`
- `docs/v10/05_V10_API_CONTRACTS.md`
- `docs/v10/06_V10_VIEWER_AND_UI_CONTRACT.md`
- `docs/v10/07_V10_SECURITY_LIMITS_AND_COMPLIANCE.md`
- `docs/v10/08_V10_SHARE_AND_PUBLIC_ACCESS_CONTRACT.md`
- `docs/v10/09_V10_ORCHESTRATOR_RULES_AND_DFM.md`
- `docs/v10/10_V10_DEPLOY_BACKUP_RESTORE.md`
- `docs/v10/11_V10_RELEASE_GATES_AND_SMOKE.md`
- `docs/v10/12_V10_OPERATIONS_AND_ADMIN.md`
- `docs/v10/13_V10_EXECUTION_ROADMAP.md`
- `docs/v10/14_V10_DRIVE_ARCHIVE_HIERARCHY.md`
- `docs/v10/15_V10_GITHUB_REPOSITORY_MAP.md`
- `docs/v10/16_V10_CONTEXT_CONTINUATION_PROTOCOL.md`
- `docs/v10/17_V10_LEGACY_RETIREMENT_MAP.md`
- `docs/v10/18_V10_EVIDENCE_AND_MANIFEST_STANDARD.md`
- `docs/v10/19_V10_FRONTEND_SURFACE_CONTRACT.md`
- `docs/v10/20_V10_FINAL_EXECUTION_CHECKLIST.md`

## Supporting Inputs

These files are useful inputs but are not active authority:
- `docs/contracts/*`
- `docs/data_model/*`
- `docs/security/*`
- `docs/compatibility/*`
- `frontend/RELEASE_GATE.md`
- `frontend/docs/*`
- `scripts/README.md`
- `STELLCODEX_ARCHIVE_ROOT/00_MASTER_INDEX/*`
- `STELLCODEX_ARCHIVE_ROOT/03_GDRIVE_ARCHIVE/*`

## Archived References

Superseded constitutions, prompts, and historical protocol generations live under:
- `docs/archive/legacy_generations/`
- `docs/archive/historical_protocols/`
- `docs/archive/old_prompts/`
- `docs/archive/frozen_reports/`
- `STELLCODEX_ARCHIVE_ROOT/99_DEPRECATED_AND_FROZEN/`

Archived references may inform future work, but they may not override the V10 package.

## Runtime Truth Handling

Repository truth must be checked against:
- current code under `backend/`, `frontend/`, `db/`, `docker/`, `infrastructure/`, `ops/`, `scripts/`
- passing release evidence and smoke output under `evidence/`
- restore proof output under `evidence/` and Drive mirrors

If code and documentation diverge, fix the documentation or fix the code. Do not preserve ambiguity.
