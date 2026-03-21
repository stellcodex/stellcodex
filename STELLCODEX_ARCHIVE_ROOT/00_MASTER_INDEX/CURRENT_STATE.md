---
archive_schema_version: "10.0"
system: "STELLCODEX"
source_domain: "ARCHIVE"
canonical_status: "ACTIVE_STATUS"
owner_layer: "SYSTEM"
related_release: "V10_CONSTITUTION_ACTIVATION"
hash_sha256: "PENDING"
last_verified_at: "2026-03-16T17:55:00Z"
sync_reference: "ARCHIVE:00_MASTER_INDEX/CURRENT_STATE.md"
---

# CURRENT_STATE

State summary:
- Archive root directory structure exists and matches the V10 constitution.
- The GitHub V10 package under `docs/v10/` is the active canonical authority set.
- The archive-root V10 constitution remains the mirrored archive copy.
- Mandatory continuity documents now exist in `00_MASTER_INDEX`.
- Repo-level authority references now resolve to the GitHub V10 package first and archived legacy references second.
- Legacy V6, V7, prompt, and frozen report authority files have been retired into explicit archive zones under `docs/archive/`.
- Canonical indexes, manifests, repository map, Drive map, and continuation protocol now exist in GitHub.
- Full recursive Drive archive inventory has been imported into the archive root.
- The GitHub V10 canonical context package has been exported into Drive under `STELLCODEX/01_CANONICAL_CONTEXT/V10_MASTER_PACKAGE/`.
- Remaining operational hygiene has been reduced to one more logrotate observation cycle.
- Inline archive metadata hashes remain queued for freeze-time normalization, but current archive integrity is already covered by `ARCHIVE_HASH_REGISTER.md`.
- Live runtime verification now passes again after fixing `rule_configs` loader drift, `orchestrator_sessions` schema drift, and smoke-gate port binding.
- Current runtime evidence bundle and the latest historical passing release bundle are both mirrored into Drive.
- Restore-from-backup runtime rebuild proof now passes through an isolated backend/worker probe.
- The live frontend cutover completed on `2026-03-16` and `https://stellcodex.com` now serves the canonical STELLCODEX manufacturing workspace shell.
- The current GitHub snapshot for the live cutover is commit `e0aa81f`, mirrored to branch `backup/20260316-live-frontend-cutover` because `main` remains protected by required checks.
- A fresh Drive backup completed after the live cutover, including DB dump `db_20260316_203205.sql.gz`, state sync, config sync, and knowledge sync.
- Cleanup policy was corrected after the live cutover so `ops/scripts/cleanup.sh` no longer deletes active production frontend runtime directories under `/var/www/stellcodex/frontend`.
- Production frontend runtime health passes again after reinstall, rebuild, and PM2 restart following the cleanup-policy correction.

Validation status:
- Archive directories present: PASS
- Continuity file set present: PASS
- Archive hash register: PASS
- GitHub V10 canonical package: PASS
- GitHub canon manifest: PASS
- Drive archive manifest: PASS
- Drive remote inventory import: PASS
- Full recursive Drive inventory import: PASS
- Restore proof register: PASS
- Canonical indexes and manifests: PASS
- Legacy authority retirement map: PASS
- Legacy relocation residual blocker: PASS
- Inline metadata hash blocker downgraded to queue: PASS
- Product surface index: PASS
- Core engines index: PASS
- STELL-AI index: PASS
- Product data model index: PASS
- Last passing release classified: PASS
- Historical passing release drive mirror registered: PASS
- Local DB backup artifact: PASS
- Local object mirror snapshot: PASS
- Object storage recovery drill: PASS
- Database restore verification: PASS
- Release gate against live runtime: PASS
- Smoke gate against live runtime: PASS
- Restore-based API rebuild proof: PASS
- Restore-based worker rebuild proof: PASS
- Current runtime evidence mirrored to Drive: PASS
- GitHub canonical context export mirrored to Drive: PASS
- Runtime restore proof coverage: PASS
- Activation evidence registration: PASS
- Live frontend cutover on public domain: PASS
- Post-cutover Drive backup: PASS
- Post-cutover cleanup policy correction: PASS
- Protected-branch backup snapshot in GitHub: PASS
