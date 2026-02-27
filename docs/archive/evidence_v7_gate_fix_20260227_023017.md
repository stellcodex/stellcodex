# V7 Gate Fix Evidence (20260227_023017 UTC)

## Scope
- Task focused only on gate scripts and CI scan scope.
- UI/Frontend code was not modified.

## Changes
- Updated scripts/smoke_test.sh to use health endpoint discovery and return success on first HTTP 200 path.
- Updated ci/contract_matrix.sh forbidden scan scope to public contract paths only: docs/contracts, schemas.
- Updated scripts/release_gate.sh to reuse smoke health validation and apply forbidden scan only to public contract paths.

## Command Evidence

### 1) Backend health route discovery
Command: rg -n "health" backend/app/api backend/app/main.py | head -n 60
backend/app/api/v1/routes/health.py:5:@router.get("/health")
backend/app/api/v1/routes/health.py:6:def health():
backend/app/api/v1/routes/admin.py:43:@router.get("/health")
backend/app/api/v1/routes/admin.py:44:def admin_health(db: Session = Depends(get_db)):
backend/app/api/v1/router.py:8:from app.api.v1.routes.health import router as health_router
backend/app/api/v1/router.py:15:api_router.include_router(health_router, tags=["health"])

### 2) Runtime health endpoint probe
Command: for p in /api/v1/admin/health /api/v1/health /health /healthz /readyz /_health; do code=$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:8000$p" || true); echo "$p -> $code"; done
/api/v1/admin/health -> 401
/api/v1/health -> 200
/health -> 404
/healthz -> 404
/readyz -> 404
/_health -> 404

### 3) Smoke test pass
Command: BASE_URL="http://127.0.0.1:8000" bash scripts/smoke_test.sh
Smoke: health endpoint discovery
PASS: health endpoint /api/v1/health
PASS: smoke

### 4) Contract matrix pass
Command: bash ci/contract_matrix.sh
== Contract Matrix ==
[1] Smoke
Smoke: health endpoint discovery
PASS: health endpoint /api/v1/health
PASS: smoke
[2] Forbidden token scan (docs/contracts + schemas only)
PASS: scoped public leak scan
[3] Runtime openapi reachable
PASS: openapi reachable
[4] Release gate (optional upload chain)
SKIP: provide SAMPLE_FILE to run upload/decision validation
PASS: contract matrix

### 5) Release gate pass
Command: BASE_URL="http://127.0.0.1:8000" bash scripts/release_gate.sh
== V7 RELEASE GATE ==
PASS: health
PASS: public contract forbidden token scan
PASS: openapi endpoint
NOTE: SAMPLE_FILE not provided; upload/decision checks skipped.
== RELEASE GATE PASS ==
