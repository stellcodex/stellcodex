---
archive_schema_version: "10.0"
system: "STELLCODEX"
source_domain: "ARCHIVE"
canonical_status: "ACTIVE_CONTINUITY"
owner_layer: "SYSTEM"
related_release: "V10_CONSTITUTION_ACTIVATION"
hash_sha256: "PENDING"
last_verified_at: "2026-03-16T17:55:00Z"
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
- Public domain `https://stellcodex.com` is currently serving the canonical frontend cut over on `2026-03-16`.
- The current live snapshot is commit `e0aa81f` and the off-main GitHub backup branch is `backup/20260316-live-frontend-cutover`.
- The latest verified post-cutover Drive DB backup is `db_20260316_203205.sql.gz`.
- `ops/scripts/cleanup.sh` was narrowed on `2026-03-16` so it no longer deletes active production frontend runtime directories.

Agent handoff rule:
- Read `docs/v10/16_V10_CONTEXT_CONTINUATION_PROTOCOL.md`, `MASTER_ARCHIVE_INDEX.md`, `CURRENT_STATE.md`, and `SYSTEM_STATE_LEDGER.md` before proposing structural changes.
- If continuity data is stale, update the relevant continuity document before continuing.
