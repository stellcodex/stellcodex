---
archive_schema_version: "10.0"
system: "STELLCODEX"
source_domain: "GITHUB"
canonical_status: "ACTIVE_REGISTER"
owner_layer: "RELEASE"
related_release: "v7-stabil-20260227"
hash_sha256: "PENDING"
last_verified_at: "2026-03-16T12:30:00Z"
sync_reference: "git tag + docs/archive/evidence_v7_gate_fix_20260227_023017.md"
---

# RELEASE_REGISTER

Known passing release records:

## v7-stabil-20260227

- Tag: `v7-stabil-20260227`
- Commit: `f0f56cf0d90bd0068f7cb2220939e3e3d719b944`
- Tagger date: `2026-02-27T13:51:18+03:00`
- Classification: PASSING RELEASE
- Evidence:
  - `docs/archive/evidence_v7_gate_fix_20260227_023017.md`
  - `docs/archive/frozen_reports/FINAL_EVIDENCE_20260227.md`
  - `docs/archive/frozen_reports/FINAL_REPORT_20260213.md`
- Drive mirror bundle:
  - `gdrive:stellcodex-genois/backups/handoff/V7_STABIL_20260227_EVIDENCE/`

Evidence summary:
- V7 release gate PASS
- smoke PASS
- openapi reachable PASS
- public contract forbidden token scan PASS

Limitations:
- This release predates V10 archive enforcement and was mirrored retroactively on `2026-03-16`.
- This register preserves known passing evidence, but V10 release evidence rules still require a contemporaneous evidence bundle + drive mirror for future releases.
