# STELLCODEX V10 Master Constitution

- Document ID: `V10-00`
- Status: `Active Canonical`
- Parent authority: `GitHub repository root /root/workspace`; archived mirror at `STELLCODEX_ARCHIVE_ROOT/01_CONSTITUTION_AND_PROTOCOLS/STELLCODEX_V10_ABSOLUTE_SYSTEM_CONSTITUTION.md`
- Related documents: `docs/v10/01_V10_SOURCE_HIERARCHY.md`, `docs/v10/03_V10_SYSTEM_ARCHITECTURE.md`, `docs/v10/14_V10_DRIVE_ARCHIVE_HIERARCHY.md`, `docs/v10/16_V10_CONTEXT_CONTINUATION_PROTOCOL.md`
- Last updated: `2026-03-16`
- Language: `English`
- Scope: `Entire STELLCODEX platform`
- Replacement rule: `Only a newer numbered V10 master constitution may replace this file. All lower-level files and runtime decisions must conform to this document.`

This document is governed by the GitHub canonical V10 package. If any lower-level file conflicts with this authority, that file must be updated or retired.

## Identity

STELLCODEX is a deterministic manufacturing decision platform.

The platform core is:
- orchestrator
- state machine enforcement
- deterministic rule engine
- DFM risk engine
- secure share engine
- audit, evidence, and operations layer

Viewer, Share, and Assistant are modules inside STELLCODEX.
MoldCodes is not a separate product. It is a manufacturing decision engine module inside STELLCODEX.

## Infrastructure Law

The infrastructure split is fixed:
- GitHub = canonical source of code, infrastructure, contracts, automation, and active V10 documentation
- Google Drive = canonical long-term archive for backups, evidence, reports, frozen references, and business memory
- Server = disposable runtime only

The server must never become archival truth.
Any server-only critical context is a defect and must be exported into GitHub or Drive.

## Source of Truth Order

Resolve conflicts in this exact order:
1. `docs/v10/00_V10_MASTER_CONSTITUTION.md` through `docs/v10/20_V10_FINAL_EXECUTION_CHECKLIST.md`
2. current verified repository reality
3. runtime evidence and passing tests
4. current valid DB, API, and runtime contracts
5. archived historical protocol generations for reference only

Prompts are never authoritative after the V10 package exists.

## Product Guarantees

The platform must remain:
- deterministic
- auditable
- recoverable
- tenant-isolated
- evidence-driven

The processing chain is fixed:
`upload -> convert -> assembly_meta -> rule_engine -> dfm_engine -> report -> pack -> archive`

Jobs must be idempotent, traceable, and recoverable.

## Change Control

New active protocol files may only be added under `docs/v10/`.
Root-level random protocol files are forbidden.
Historical reports, prompts, and superseded constitutions must live under `docs/archive/` or `STELLCODEX_ARCHIVE_ROOT/99_DEPRECATED_AND_FROZEN/`.

## Continuity Rule

Future sessions must resume from:
- `docs/v10/16_V10_CONTEXT_CONTINUATION_PROTOCOL.md`
- `STELLCODEX_ARCHIVE_ROOT/00_MASTER_INDEX/CONTINUATION_CONTEXT.md`
- `STELLCODEX_ARCHIVE_ROOT/00_MASTER_INDEX/CURRENT_STATE.md`

Context loss is a SEV-0 failure.
