# Scripts

- smoke_test.sh: basic health/openapi
- smoke_gate.sh: end-to-end regression gate (upload -> status -> view -> share + jpg/dxf/step checks)
- release_gate.sh: V10 blocking checks + optional upload + share contract validation
- e2e_smoke.sh: authenticated end-to-end smoke flow for upload, agent, share, and frontend route checks
- leak_scan_repo.sh: public-contract forbidden token scan for `docs/contracts` and `schemas`
- backup_db.sh: daily DB dump
- backup_object_mirror.sh: object mirror via MinIO client (mc) or docker cp fallback; defaults to local path target under `./backups/object_mirror`
- object_restore_drill.sh: restores the local object mirror into an isolated MinIO probe and verifies object visibility via S3 listing
- runtime_restore_probe.sh: restores the latest DB dump, mounts the object mirror into isolated Redis/MinIO/backend/worker probes, and verifies a STEP upload can complete end-to-end
- weekly_restore_gate.sh: restore latest DB dump into a temporary database and rerun release gate; can optionally run smoke gate too

## smoke_gate.sh

```
./scripts/smoke_gate.sh
```

Optional env vars:

```
API_BASE=http://127.0.0.1:18000/api/v1 FRONT_BASE=http://127.0.0.1:3010 STEP_SAMPLE=/path/to/file.STEP ./scripts/smoke_gate.sh
```

## weekly_restore_gate.sh

```
./scripts/weekly_restore_gate.sh
```

Optional env vars:

```
BACKUP_DIR=./backups RESTORE_DB_NAME=stellcodex_restore_probe RUN_SMOKE_GATE=1 ./scripts/weekly_restore_gate.sh
```

## e2e_smoke.sh

```
./scripts/e2e_smoke.sh
```

Optional env vars:

```
API_BASE=http://127.0.0.1:18000/api/v1 FRONT_BASE=http://127.0.0.1:3010 REPORT_DIR=./evidence ./scripts/e2e_smoke.sh
```
