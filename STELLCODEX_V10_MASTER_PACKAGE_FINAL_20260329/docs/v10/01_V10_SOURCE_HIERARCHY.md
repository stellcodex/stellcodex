# STELLCODEX V10 Source Hierarchy

- Document ID: `V10-01`
- Status: `Active Canonical`
- Parent authority: `docs/v10/00_V10_MASTER_CONSTITUTION.md`
- Last updated: `2026-03-29`
- Language: `English`
- Scope: `Authority resolution, repository truth handling, and archive separation`

## Absolute Source of Truth Order

1. **V10 Master Protocol Documents**: `docs/v10/00` to `20`.
2. **Canonical Manifests and Indexes**: `docs/manifests/` and `docs/indexes/`.
3. **Repository Reality**: Current code and configuration in GitHub.
4. **Archive References**: Historical documentation and backups (Reference only).
5. **Prompts**: Non-authoritative history only.

**Any conflict between prompts and these documents must be resolved in favor of these documents.**

## Active Canonical Set (Frozen V10)

The following files under `docs/v10/` constitute the absolute canonical V10 documentation set. No other files in the repository carry active authority.

- `00` to `20` numbered documents.

## Repository Mapping

- **Product Code**: `backend/`, `frontend/`, `db/`.
- **Infrastructure**: `docker/`, `infrastructure/`, `ops/`.
- **Support Engines**: `_canonical_repos/stell-ai/`, `_canonical_repos/orchestra/`, `_canonical_repos/infra/`.
- **Manifests & Indexes**: `docs/manifests/`, `docs/indexes/`.

## Authority Mapping Rules

- GitHub is the canonical source for logic and documentation.
- Drive is the canonical source for archive, evidence, and frozen references.
- Server is for disposable execution only. No unique authority may live there.
- All evidence must pass through the `V10_EVIDENCE_AND_MANIFEST_STANDARD`.

## Conflict Resolution

If code and documentation diverge, the Master Protocol documentation prevails unless it is demonstrably stale, in which case both documentation and code must be updated to the new V10-00 compliant state. Ambiguity is a failure.
