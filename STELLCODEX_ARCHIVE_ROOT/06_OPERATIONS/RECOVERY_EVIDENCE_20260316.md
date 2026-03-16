---
archive_schema_version: "10.0"
system: "STELLCODEX"
source_domain: "ARCHIVE"
canonical_status: "ACTIVE_EVIDENCE"
owner_layer: "OPERATIONS"
related_release: "V10_CONSTITUTION_ACTIVATION"
hash_sha256: "PENDING"
last_verified_at: "2026-03-16T11:18:40Z"
sync_reference: "local runtime evidence generated on 2026-03-16"
---

# RECOVERY_EVIDENCE_20260316

## Scope

Generate fresh local recovery evidence after V10 archive activation:
- DB backup artifact
- object storage mirror snapshot
- restore gate evidence
- current runtime release gate evidence
- current runtime smoke gate evidence

## Commands Run

1. `OUT_DIR=/root/workspace/backups DB_CONTAINER=deploy_postgres_1 DB_USER=stellcodex DB_NAME=stellcodex ./scripts/backup_db.sh`
2. `DST_PATH=/root/workspace/backups/object_mirror MINIO_CONTAINER=deploy_minio_1 BUCKET=stellcodex ./scripts/backup_object_mirror.sh`
3. `DB_CONTAINER=deploy_postgres_1 DB_USER=stellcodex DB_NAME=stellcodex BACKUP_DIR=/root/workspace/backups BASE_URL=http://127.0.0.1:18000 API_BASE=http://127.0.0.1:18000/api/v1 FRONT_BASE=http://127.0.0.1:3010 RUN_RELEASE_GATE=1 RUN_SMOKE_GATE=1 ./scripts/weekly_restore_gate.sh`
4. `BASE_URL=http://127.0.0.1:18000 ./scripts/release_gate.sh > /root/workspace/evidence/release_gate_v10_activation_20260316.txt 2>&1`
5. `df -h / /root/workspace /var/lib/docker`
6. `docker restart deploy_backend_1 deploy_worker_1`
7. `API_BASE=http://127.0.0.1:18000/api/v1 FRONT_BASE=http://127.0.0.1:3010 ./scripts/smoke_gate.sh`
8. `./scripts/object_restore_drill.sh`
9. `./scripts/runtime_restore_probe.sh`
10. `rclone copy /tmp/V10_RUNTIME_RECOVERY_20260316_111840 gdrive:stellcodex-genois/backups/handoff/V10_RUNTIME_RECOVERY_20260316_111840`

## Artifacts Produced

- Local DB dump: `/root/workspace/backups/db_stellcodex_20260316_124352.sql.gz`
- DB dump size: `597K`
- Local object mirror root: `/root/workspace/backups/object_mirror/stellcodex`
- Object mirror footprint: `5.2M`
- Object mirror file count: `456`
- Restore gate evidence: `/root/workspace/evidence/weekly_restore_gate_output.txt`
- Release gate evidence: `/root/workspace/evidence/release_gate_v10_activation_20260316.txt`
- Smoke gate evidence: `/root/workspace/evidence/smoke_gate_output.txt`
- Object restore drill evidence: `/root/workspace/evidence/object_restore_drill_output.txt`
- Runtime restore probe evidence: `/root/workspace/evidence/runtime_restore_probe_output.txt`
- Drive recovery bundle: `gdrive:stellcodex-genois/backups/handoff/V10_RUNTIME_RECOVERY_20260316_111840/`

## Results

- DB backup: PASS
- Object mirror snapshot: PASS
- Release gate against live API (`127.0.0.1:18000`): PASS
- Smoke gate against live API/UI (`127.0.0.1:18000` / `127.0.0.1:3010`): PASS
- Object restore drill against isolated MinIO probe: PASS
- Restore-from-backup runtime probe against isolated backend/worker stack: PASS
- Restore gate: PASS
- Drive mirror for the current runtime evidence bundle: PASS

Corrective actions required before PASS:
- Oversized runtime audit log was truncated to clear host disk exhaustion.
- `rule_configs` runtime loader was aligned to the live database schema.
- `orchestrator_sessions` runtime model/state handling was aligned to the live database schema.
- `smoke_gate.sh` preview fetches were corrected to use the active API origin instead of hardcoded port `8000`.

## Interpretation

- Database recovery is now proven by a successful temp-database restore.
- Object storage recovery is now proven by a successful isolated MinIO restore drill from the local mirror.
- API and worker paths now pass both live-runtime validation and restore-from-backup validation.
- Cross-domain evidence closure is now present for the current runtime bundle.
- Full restore closure is now proven across database, object storage, worker, and API recovery.
