# STELLCODEX V10 Drive Archive Hierarchy

- Document ID: `V10-14`
- Status: `Active Canonical`
- Parent authority: `docs/v10/00_V10_MASTER_CONSTITUTION.md`, `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- Related documents: `docs/v10/10_V10_DEPLOY_BACKUP_RESTORE.md`, `docs/v10/18_V10_EVIDENCE_AND_MANIFEST_STANDARD.md`, `docs/indexes/DRIVE_INDEX.md`
- Last updated: `2026-03-16`
- Language: `English`
- Scope: `Operator-readable Google Drive structure and folder purposes`
- Replacement rule: `Drive hierarchy changes must update this file before any archive automation or operator handoff changes.`

This document is governed by `docs/v10/00_V10_MASTER_CONSTITUTION.md` and `docs/v10/01_V10_SOURCE_HIERARCHY.md`. If any lower-level file conflicts with these authorities, this file must be updated to comply.

## Canonical Drive Root

`Google Drive / STELLCODEX /`

## Required Hierarchy

- `00_ADMIN/`
  - `OWNERSHIP_AND_ACCESS/`: owner list, access policy, recovery contacts
  - `CONTACTS/`: operator, maintainer, and escalation contacts
  - `OPERATION_RULES/`: operator runbooks and archive access rules
- `01_CANONICAL_CONTEXT/`
  - `V10_MASTER_PACKAGE/`: exported V10 canonical docs
  - `SOURCE_HIERARCHY/`: authority map and repo truth notes
  - `REPO_MAP/`: repository map exports
  - `DRIVE_MAP/`: Drive purpose map exports
  - `CONTINUATION_CONTEXT/`: session continuity bundles
- `02_BACKUPS/`
  - `DATABASE/`
  - `OBJECT_STORAGE/`
  - `SERVER_EXPORTS/`
  - `SNAPSHOTS/`
  - `WEEKLY_RESTORE_BUNDLES/`
- `03_EVIDENCE/`
  - `RELEASE_GATES/`
  - `SMOKE_TESTS/`
  - `RESTORE_TESTS/`
  - `SECURITY_CHECKS/`
  - `AUDIT_EXPORTS/`
  - `KNOWLEDGE_ENGINE/`
  - `TOOL_ECOSYSTEM/`
  - `STABILIZATION/`
- `04_REPORTS/`
  - `SYSTEM_STATUS/`
  - `FORENSIC_AUDITS/`
  - `MILESTONE_REPORTS/`
  - `UI_REPORTS/`
  - `MIGRATION_REPORTS/`
- `05_PROJECT_MEMORY/`
  - `DECISIONS/`
  - `RESOLVED_CASES/`
  - `SSOT_EXPORTS/`
  - `EVENT_SUMMARIES/`
- `06_HANDOFF/`
  - `EXECUTION_BUNDLES/`
  - `CONTINUATION_BUNDLES/`
  - `RECOVERY_BUNDLES/`
- `07_ARCHIVE/`
  - `LEGACY_PROTOCOLS/`
  - `OLD_MASTER_PROMPTS/`
  - `RETIRED_DOCS/`
  - `HISTORICAL_SNAPSHOTS/`

## Drive Rules

- canonical docs are separate from evidence
- backups are separate from reports
- legacy materials are isolated from active context
- naming is deterministic and English only
- every bundle includes a manifest and evidence reference
