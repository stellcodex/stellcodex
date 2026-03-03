# Scripts

- smoke_test.sh: basic health/openapi
- smoke_gate.sh: end-to-end regression gate (upload -> status -> view -> share + jpg/dxf/step checks)
- release_gate.sh: V7 blocking checks + optional upload chain + decision_json validation
- leak_scan_repo.sh: public-contract forbidden token scan for `docs/contracts` and `schemas`
- backup_db.sh: daily DB dump
- backup_object_mirror.sh: object mirror via MinIO client (mc)
- weekly_restore_gate.sh: weekly restore gate template

## smoke_gate.sh

```
./scripts/smoke_gate.sh
```

Optional env vars:

```
API_BASE=http://127.0.0.1:8000/api/v1 FRONT_BASE=http://127.0.0.1:3010 STEP_SAMPLE=/path/to/file.STEP ./scripts/smoke_gate.sh
```
