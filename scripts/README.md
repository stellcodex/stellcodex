# Scripts

- smoke_test.sh: basic health/openapi
- release_gate.sh: V7 blocking checks + optional upload chain + decision_json validation
- leak_scan_repo.sh: repo-wide forbidden token scan (prevents accidental leaks)
- backup_db.sh: daily DB dump
- backup_object_mirror.sh: object mirror via MinIO client (mc)
- weekly_restore_gate.sh: weekly restore gate template
