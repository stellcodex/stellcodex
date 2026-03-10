# Canonical Repo Layout

Required root directories:

- `stell-ai/`
- `orchestra/`
- `stellcodex/`
- `infra/`

Each boundary root must contain:

- `/src`
- `/docs`
- `/deploy`
- `/scripts`
- `/tests`

Compatibility mapping currently used:

- `stell-ai/src -> AI/stell_ai`
- `orchestra/src -> ops/orchestra/orchestrator`
- `stellcodex/src -> stellcodex_v7/backend/app`
- `infra/deploy -> stellcodex_v7/infrastructure/deploy`

This preserves active runtime while enabling immediate migration to independent repositories.
