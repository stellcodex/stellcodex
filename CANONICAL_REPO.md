STELLCODEX canonical git repository: `/root/workspace`

Canonical source of code and infrastructure is GitHub remote `stellcodex/stellcodex.git`.

Canonical top-level repo layout:
- `docs/`
- `backend/` (compat symlink -> `stellcodex_v7/backend`)
- `frontend/` (compat symlink -> `stellcodex_v7/frontend`)
- `orchestra/` (compat symlink -> `ops/orchestra`)
- `infra/` (compat symlink -> `stellcodex_v7/infrastructure`)
- `scripts/`
- `ops/`
- `archive_legacy/`

Legacy duplicate working trees are non-canonical and must not be used as source of truth:
- `/var/www/stellcodex`
- `/root/stell`
- `/tmp/stellcodex_*`
