# STELLCODEX V10 Evidence And Manifest Standard

- Document ID: `V10-18`
- Status: `Active Canonical`
- Parent authority: `docs/v10/00_V10_MASTER_CONSTITUTION.md`, `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- Related documents: `docs/v10/11_V10_RELEASE_GATES_AND_SMOKE.md`, `docs/v10/14_V10_DRIVE_ARCHIVE_HIERARCHY.md`, `docs/manifests/DOC_MIGRATION_MANIFEST.md`
- Last updated: `2026-03-16`
- Language: `English`
- Scope: `Required contents of manifests, evidence bundles, and archive references`
- Replacement rule: `Evidence and manifest changes must update this file before new bundle formats are used.`

This document is governed by `docs/v10/00_V10_MASTER_CONSTITUTION.md` and `docs/v10/01_V10_SOURCE_HIERARCHY.md`. If any lower-level file conflicts with these authorities, this file must be updated to comply.

## Required Manifest Types

- document migration manifest
- legacy retirement manifest
- file authority map
- final consolidation report
- release register
- restore proof register

## Bundle Minimum

Every release or recovery bundle must contain:
- a manifest
- the main evidence outputs
- enough metadata to map the bundle back to GitHub files and runtime scripts
- a Drive mirror reference or destination

## Evidence Rule

Never claim PASS without evidence.
Never claim completion of a restore area without the matching proof output.
Never keep evidence only on the runtime server when it belongs in Drive.
