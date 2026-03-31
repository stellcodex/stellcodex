# DRIVE REATTACH FLOW

## Purpose

This document defines how Google Drive-managed state is reattached after a GitHub-first rebuild of the STELLCODEX runtime.

## Principle

Drive reattachment happens only **after** the runtime has been rebuilt from canonical GitHub repositories.

Do not attempt to reconstruct system code truth from Drive.

## Drive Reattachment Scope

The following categories are expected to come from Drive:

- backups
- memory
- evidence
- reports
- release artifacts
- archives
- historical records

## Canonical Root

The canonical Drive root is:

- `STELLCODEX/`

Expected primary folders under this root:

- `ARCHIVE`
- `OPS`
- `DATASETS`
- `RELEASES`
- `MEMORY`
- `EVIDENCE`
- `BACKUPS`
- `01_CANONICAL_CONTEXT`

## Legacy Folders

Legacy or earlier-generation roots may exist, for example:

- `STELLCODEX_BACKUPS`
- `stellcodex`
- `stellcodex-genois`
- `STELL`

These must not be treated as active canonical roots.

They should be classified as:

- legacy imports
- historical archives
- migration-era residue

## Reattach Sequence

1. Confirm runtime rebuild from GitHub is complete
2. Confirm service health is available
3. Confirm env/materialization is complete
4. Reattach Drive backup paths
5. Reattach memory/evidence paths
6. Verify archive/release visibility
7. Run restore/smoke validation

## Validation Checks

Drive reattachment is considered complete only if:

- backup paths are reachable
- memory paths are reachable
- evidence/report paths are reachable
- legacy roots are not being treated as active truth
- runtime health remains stable after reattachment

## Summary

Drive does not rebuild the platform.

Drive restores long-lived state after GitHub rebuilds the platform runtime.
