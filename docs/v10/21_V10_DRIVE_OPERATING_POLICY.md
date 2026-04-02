# V10 Drive Operating Policy

## Purpose
This document defines the only valid Google Drive archive structure for STELLCODEX V10.

## Canonical Rule
The only active permanent Google Drive root is:

STELLCODEX_V10/

No other root-level STELLCODEX, STELL, or stellcodex folder is considered active.
Any previous root, duplicate structure, or legacy folder must exist only under:

STELLCODEX_V10/ARCHIVE/

## Allowed Top-Level Folders
STELLCODEX_V10/
- 01_CANONICAL_CONTEXT
- BACKUPS
- EVIDENCE
- MEMORY
- DATASETS
- OPS
- RELEASES
- ARCHIVE

## Folder Meanings

### 01_CANONICAL_CONTEXT
Stores the master package, architecture rules, source-of-truth documents, and locked operating constitutions.

### BACKUPS
Stores database dumps, snapshots, config backups, and source/runtime backup bundles.

### EVIDENCE
Stores proofs, smoke results, release-gate outputs, validation reports, and runtime verification artifacts.

### MEMORY
Stores self-learning exports, case logs, eval outputs, retrieval memory exports, and pattern signals.

### DATASETS
Stores training inputs, raw datasets, transformed datasets, and import-ready corpus material.

### OPS
Stores operational runbooks, maintenance outputs, infra/export artifacts, and recurring ops results.

### RELEASES
Stores release bundles, deploy artifacts, release snapshots, and publish-ready packages.

### ARCHIVE
Stores pre-V10 roots, legacy folders, duplicate structures, residual migrations, and deprecated material.

## Write Rules
- Backups must be written only to `STELLCODEX_V10/BACKUPS`
- Evidence and reports must be written only to `STELLCODEX_V10/EVIDENCE`
- Learning memory, evals, case logs, and pattern outputs must be written only to `STELLCODEX_V10/MEMORY`
- Datasets and training inputs must be written only to `STELLCODEX_V10/DATASETS`
- Operations outputs and maintenance exports must be written only to `STELLCODEX_V10/OPS`
- Release bundles and release artifacts must be written only to `STELLCODEX_V10/RELEASES`
- Any deprecated or uncertain structure must be written only to `STELLCODEX_V10/ARCHIVE`

## Forbidden States
The following states are forbidden:
- writing new files to Google Drive root
- creating parallel roots such as `STELLCODEX`, `stellcodex`, `STELL`, or similar
- treating any legacy folder as canonical truth
- storing active files directly inside `ARCHIVE`
- mixing backups, evidence, memory, datasets, and release artifacts in the same folder
- restoring old folder names as active roots

## Source of Truth Hierarchy
- GitHub = canonical source for code and operating policy
- Google Drive = canonical permanent archive, backup, evidence, and data store
- Runtime/server = disposable execution environment only

## Archive Rule
All legacy or pre-V10 structures must live only under:

`STELLCODEX_V10/ARCHIVE/`

Examples:
- `STELLCODEX_preV10_root`
- `STELL_legacy`
- `stellcodex_legacy`
- `stellcodex_genois_legacy`

## Enforcement Intent
All future backup jobs, restore jobs, evidence exports, memory exports, dataset imports, and operations tooling must target `STELLCODEX_V10` only.

No future automation is allowed to create a new root-level Drive folder for STELLCODEX.
