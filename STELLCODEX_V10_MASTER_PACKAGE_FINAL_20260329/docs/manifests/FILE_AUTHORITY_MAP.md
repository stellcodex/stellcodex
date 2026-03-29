# STELLCODEX File Authority Map

- Status: `Active Canonical Manifest`
- Parent authority: `docs/v10/00_V10_MASTER_CONSTITUTION.md`, `docs/v10/01_V10_SOURCE_HIERARCHY.md`
- Last updated: `2026-03-29`
- Language: `English`

## Authoritative Ownership

| Directory / File | Authority Source | Ownership Role | Status |
| --- | --- | --- | --- |
| `docs/v10/` | GitHub Repo | Master Protocol | ACTIVE |
| `backend/` | GitHub Repo | API / Persistence | ACTIVE |
| `frontend/` | GitHub Repo | UI / Viewer | FROZEN |
| `_canonical_repos/` | GitHub Repo | Logic / Infra | ACTIVE |
| `STELLCODEX_ARCHIVE_ROOT/` | Drive (Mirror) | Archive / Backup | ACTIVE |
| `evidence/` | Runtime Gen | Proof of Execution | DYNAMIC |
| `docs/archive/` | GitHub Repo | Legacy History | RETIRED |
| `_jobs/` | Server | Runtime State | DISPOSABLE |

## Forbidden Authority Confusion
- Never treat `_jobs/` or server runtime as source of truth for protocol.
- Never treat legacy V7 documentation (in `docs/archive/` or `docs/v6/`) as active authority.
- Never treat local `evidence/` as permanent without Drive archival.
