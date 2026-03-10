# System Architecture Map (V7 Audit)

Audit timestamp: 2026-03-08 (UTC)
Evidence bundle: `/root/workspace/evidence/v7_fix_run_20260308T032241Z`

## Services
- `deploy_backend_1` (API, port `18000`)
- `deploy_worker_1` (worker execution)
- `deploy_postgres_1` (DB)
- `deploy_minio_1` (object storage)
- `deploy_redis_1` (queue/rate-limit cache)

## Repository map
- Backend: `/root/workspace/stellcodex_v7/backend`
- Frontend: `/root/workspace/stellcodex_v7/frontend`
- Worker pipeline: `/root/workspace/stellcodex_v7/backend/app/workers`
- Orchestrator: `/root/workspace/stellcodex_v7/backend/app/core/orchestrator.py`
- Rule engine: `/root/workspace/stellcodex_v7/backend/app/core/rule_engine.py`
- DFM engine: `/root/workspace/stellcodex_v7/backend/app/core/dfm_engine.py`
- Share engine: `/root/workspace/stellcodex_v7/backend/app/api/v1/routes/share.py`

## Dependencies
- Backend depends on Postgres + Redis + MinIO.
- Worker depends on Postgres + Redis + MinIO + conversion toolchain.
- Frontend depends on backend API contract.

## Missing modules / conflicts
- No runtime-blocking missing module found for V7 checks.
- Orchestrator logic remains multi-module (`core/orchestrator.py` + `services/orchestrator_engine.py`) but runtime contract checks pass.

## Section verdict
PASS
