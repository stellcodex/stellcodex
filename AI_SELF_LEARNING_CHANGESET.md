# AI Self-Learning Changeset

## Report Artifact

- [AI_SELF_LEARNING_REPORT.md](/root/workspace/AI_SELF_LEARNING_REPORT.md)

## Relevant Repo Heads At Closure

- `stellcodex/stellcodex` base HEAD: `02c71ec`
- `stellcodex/stell-ai` base HEAD: `1ef176e`
- `stellcodex/orchestra` base HEAD: `b2ef87e`
- `stellcodex/infra` base HEAD: `0dfaf22`

## Commit Status

No self-learning-specific commit was created in this closure pass.

Relevant changes remain as working-tree modifications in the canonical repos listed below.

## Changed Files

### `stellcodex/stellcodex`

- [/.env.example](/root/workspace/.env.example)
- [backend/Dockerfile.backend](/root/workspace/backend/Dockerfile.backend)
- [backend/app/api/v1/router.py](/root/workspace/backend/app/api/v1/router.py)
- [backend/app/api/v1/routes/internal_runtime.py](/root/workspace/backend/app/api/v1/routes/internal_runtime.py)
- [backend/app/api/v1/routes/ai.py](/root/workspace/backend/app/api/v1/routes/ai.py)
- [backend/app/core/config.py](/root/workspace/backend/app/core/config.py)
- [backend/app/models/__init__.py](/root/workspace/backend/app/models/__init__.py)
- [backend/app/models/ai_learning.py](/root/workspace/backend/app/models/ai_learning.py)
- [backend/app/services/ai_learning.py](/root/workspace/backend/app/services/ai_learning.py)
- [backend/app/startup.py](/root/workspace/backend/app/startup.py)

### `stellcodex/stell-ai`

- [runtime_app/lib/backend_client.py](/root/workspace/_canonical_repos/stell-ai/runtime_app/lib/backend_client.py)
- [runtime_app/main.py](/root/workspace/_canonical_repos/stell-ai/runtime_app/main.py)

### `stellcodex/orchestra`

- [runtime_app/lib/backend_client.py](/root/workspace/_canonical_repos/orchestra/runtime_app/lib/backend_client.py)
- [runtime_app/main.py](/root/workspace/_canonical_repos/orchestra/runtime_app/main.py)

### `stellcodex/infra`

- [deploy/docker-compose.yml](/root/workspace/_canonical_repos/infra/deploy/docker-compose.yml)

## What These Changes Cover

- structured case logging
- memory table creation and persistence
- eval result persistence
- similarity retrieval and clustering
- signal generation:
  - `pattern_signal`
  - `recovery_signal`
  - `optimization_signal`
- STELL.AI memory-augmented decision payloads
- Orchestra run logging and recovery-input propagation
- admin observability endpoints
- Drive snapshot export wiring
- runtime fixes required to pass real acceptance validation
