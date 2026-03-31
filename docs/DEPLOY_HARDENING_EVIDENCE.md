# Deploy Hardening Evidence

## Final dependency manifest
- `backend/requirements.txt` pinned and canonicalized.

## Startup import audit summary
Generated via:
```bash
PYTHONPATH=backend python backend/scripts/startup_import_audit.py
```
Output saved at:
- `docs/STARTUP_IMPORT_AUDIT.txt`

## Env contract summary
- `docs/ENV_CONTRACT_SUMMARY.md`

## Static OpenAPI/route-group verification
Command:
```bash
cd backend && DATABASE_URL='postgresql+psycopg2://u:p@localhost:5432/db' JWT_SECRET='12345678901234567890123456789012' STATIC_OPENAPI_ONLY=1 SKIP_INSTALL=1 SKIP_MIGRATIONS=1 ./scripts/cold_boot_verify.sh
```
Result:
- `STATIC_OPENAPI_VERIFY_OK`

## Cold-boot verification status in this environment
- Full runtime cold-boot (DB connect + migration + HTTP probe) requires reachable PostgreSQL and package index access.
- This execution environment does not provide those prerequisites, so full online boot probes were prepared as script automation but not executed end-to-end here.
- Canonical verifier: `backend/scripts/cold_boot_verify.sh`
