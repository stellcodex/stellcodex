# Scripts

- smoke_test.sh: basic health/openapi
- smoke_gate.sh: end-to-end regression gate (upload -> status -> view -> share + jpg/dxf/step checks)
- release_gate.sh: V7 blocking checks + optional upload + share contract validation
- leak_scan_repo.sh: public-contract forbidden token scan for `docs/contracts` and `schemas`
- backup_db.sh: daily DB dump
- backup_object_mirror.sh: object mirror via MinIO client (mc) or docker cp fallback; defaults to local path target under `./backups/object_mirror`
- weekly_restore_gate.sh: restore latest DB dump into a temporary database and rerun release gate; can optionally run smoke gate too

## smoke_gate.sh

```
./scripts/smoke_gate.sh
```

Optional env vars:

```
API_BASE=http://127.0.0.1:8000/api/v1 FRONT_BASE=http://127.0.0.1:3010 STEP_SAMPLE=/path/to/file.STEP ./scripts/smoke_gate.sh
```

## weekly_restore_gate.sh

```
./scripts/weekly_restore_gate.sh
```

Optional env vars:

```
BACKUP_DIR=./backups RESTORE_DB_NAME=stellcodex_restore_probe RUN_SMOKE_GATE=1 ./scripts/weekly_restore_gate.sh
```
