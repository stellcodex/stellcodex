# STELLCODEX V10 Master Constitution

- Document ID: `V10-00`
- Status: `Active Canonical`
- Parent authority: `GitHub repository root /root/workspace`; archived mirror at `STELLCODEX_ARCHIVE_ROOT/01_CONSTITUTION_AND_PROTOCOLS/STELLCODEX_V10_ABSOLUTE_SYSTEM_CONSTITUTION.md`
- Last updated: `2026-03-29`
- Language: `English`
- Scope: `Entire STELLCODEX platform`

## Absolute Authority

This document is the supreme authority for the STELLCODEX V10 Master Package. All lower-level files, code, and runtime decisions must conform to this constitution. V7 and earlier protocol generations are retired and carry no active authority.

## Infrastructure Law

The infrastructure split is absolute:
- **GitHub**: Canonical source of truth for code, infrastructure, contracts, automation, and active V10 documentation.
- **Google Drive**: Permanent archive for backups, evidence, reports, frozen references, and long-term business memory.
- **Server**: Disposable runtime only. Any critical context must be exported to GitHub or Drive.

## Authority Separation

- **STELLCODEX**: Product, workflow, and UI authority.
- **STELL-AI**: Independent intelligence authority.
- **ORCHESTRA**: Execution and state authority.
- **Backend**: Gateway, authentication, and persistence only.

## Source of Truth Order

Resolve conflicts in this exact order:
1. `docs/v10/` Master Package documentation (dated 2026-03-29).
2. `docs/manifests/` and `docs/indexes/` (dated 2026-03-29).
3. Current verified repository reality (GitHub).
4. Runtime evidence and passing tests.
5. Archived historical protocol generations (Reference only).

**Prompts are never authoritative.**

## UI and Frontend Freeze

The STELLCODEX V10 UI is frozen. Frontend rebuilds, redesigns, or major refactors are forbidden. Completed phases remain closed.

## Product Guarantees

The platform must remain:
- **Deterministic**: Every decision is reproducible.
- **Auditable**: Full trace from upload to archive.
- **Fail-Closed**: No unauthorized access or data leaks.
- **Identity Disciplined**: Public identity is `file_id`-only. No internal leaks.

## Continuity Rule

Future sessions must resume from `docs/v10/16_V10_CONTEXT_CONTINUATION_PROTOCOL.md`. Context loss is a SEV-0 failure.
