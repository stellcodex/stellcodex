---
archive_schema_version: "10.0"
system: "STELLCODEX"
source_domain: "ARCHIVE"
canonical_status: "ACTIVE_CONTINUITY"
owner_layer: "SYSTEM"
related_release: "V10_CONSTITUTION_ACTIVATION"
hash_sha256: "PENDING"
last_verified_at: "2026-03-16T12:30:00Z"
sync_reference: "ARCHIVE:00_MASTER_INDEX/CONTINUATION_CONTEXT.md"
---

# CONTINUATION_CONTEXT

Current binding authority:
- The GitHub canonical V10 package under `docs/v10/` is the sole active documentation authority.
- The archive-root V10 constitution is the mirror copy of that canonical package.

Operational baseline:
- GitHub remains the canonical system definition.
- Google Drive remains the permanent artifact archive.
- Runtime remains stateless and rebuildable from GitHub + Drive.

Agent handoff rule:
- Read `docs/v10/16_V10_CONTEXT_CONTINUATION_PROTOCOL.md`, `MASTER_ARCHIVE_INDEX.md`, `CURRENT_STATE.md`, and `SYSTEM_STATE_LEDGER.md` before proposing structural changes.
- If continuity data is stale, update the relevant continuity document before continuing.
