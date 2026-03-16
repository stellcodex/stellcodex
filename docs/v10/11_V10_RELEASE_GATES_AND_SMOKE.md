# STELLCODEX V10 Release Gates And Smoke

- Document ID: `V10-11`
- Status: `Active Canonical`
- Parent authority: `docs/v10/00_V10_MASTER_CONSTITUTION.md`, `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- Related documents: `docs/v10/10_V10_DEPLOY_BACKUP_RESTORE.md`, `docs/v10/18_V10_EVIDENCE_AND_MANIFEST_STANDARD.md`, `docs/v10/20_V10_FINAL_EXECUTION_CHECKLIST.md`
- Last updated: `2026-03-16`
- Language: `English`
- Scope: `Release blocking gates, smoke expectations, and evidence closure`
- Replacement rule: `Release-gate changes require synchronized updates to scripts, evidence, and this document.`

This document is governed by `docs/v10/00_V10_MASTER_CONSTITUTION.md` and `docs/v10/01_V10_SOURCE_HIERARCHY.md`. If any lower-level file conflicts with these authorities, this file must be updated to comply.

## Required Gates

- release gate against the live runtime
- smoke gate against the live runtime
- weekly restore gate
- object restore drill
- runtime restore probe from backup material

## Minimum PASS Rule

A release is valid only when:
- code builds or compiles where required
- health checks pass
- smoke output passes
- restore coverage passes across DB, object storage, worker, and API
- evidence is mirrored into Drive

## Current Proof Anchors

- `evidence/release_gate_v10_activation_20260316.txt`
- `evidence/smoke_gate_output.txt`
- `evidence/weekly_restore_gate_output.txt`
- `evidence/object_restore_drill_output.txt`
- `evidence/runtime_restore_probe_output.txt`
- current Drive bundle: `gdrive:stellcodex-genois/backups/handoff/V10_RUNTIME_RECOVERY_20260316_111840/`
