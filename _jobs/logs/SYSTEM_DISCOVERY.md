# STELLCODEX SYSTEM DISCOVERY REPORT
Generated: 2026-03-08T14:48:00Z

## OS & Hardware
- **OS:** Ubuntu 20.04.6 LTS (Focal Fossa)
- **Kernel:** Linux 5.4.0-216-generic x86_64
- **CPU:** 2 cores
- **RAM:** 3.8Gi total / 2.6Gi used / 982Mi available
- **Disk:** 56G total / 19G used / 35G available (35% used)
- **Swap:** 2.9Gi (2.8Gi used — near capacity, monitor)

## Docker Containers (Running)
| Container | Status | Ports |
|-----------|--------|-------|
| deploy_backend_1 | Up (healthy) | 0.0.0.0:18000->8000/tcp |
| deploy_worker_1 | Up | — |
| deploy_minio_1 | Up (healthy) | 19000:9000, 19001:9001 |
| deploy_postgres_1 | Up (healthy) | 15432:5432 |
| deploy_redis_1 | Up (healthy) | 16379:6379 |
| orchestra_orchestrator_1 | Up 37h | 7010:7010 |
| orchestra_litellm_1 | Up 2d | 4000:4000 |
| orchestra_ollama | Up 2d | 11434 |
| orchestra_stellai_1 | Up 3d | 7020:7020 |

## PM2 Processes
| ID | Name | Status | Uptime |
|----|------|--------|--------|
| 3 | stell-event-listener | online | — |
| 1 | stell-webhook | online | 36h |
| 0 | stellcodex-next | online | 36h |

## Database (PostgreSQL :15432)
- **Version:** j1a2b3c4d5e6 (Knowledge Engine — CURRENT)
- **29 tables** including: knowledge_records, knowledge_index_jobs (NEW)

## Object Storage
- MinIO running on :19000/:19001
- Storage backend: volume-mounted (v7_minio_data)

## Environment Variables
- DATABASE_URL: postgresql+psycopg2://stellcodex:stellcodex@postgres:5432/stellcodex
- REDIS_URL: redis://redis:6379/0
- JWT_ALG: HS256
