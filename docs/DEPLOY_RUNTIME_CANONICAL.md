# STELLCODEX Backend Canonical Deploy Runtime (Zero-Drift)

## 1) Canonical runtime version
- **Python: 3.11.9** (authoritative for Render + Docker).
- Runtime pin locations:
  - `backend/runtime.txt`
  - `backend/Dockerfile`
  - `backend/Dockerfile.backend`

## 2) Required env vars (minimum boot contract)
These are the only strict boot blockers:
- `DATABASE_URL` (must use `postgresql://` or `postgresql+psycopg2://`)
- `JWT_SECRET` (or `SECRET_KEY` / `APP_SECRET` / `SIGNING_KEY`; min length 32)

### Recommended required-for-production env
- `REDIS_URL` (required for queue workers/rate-limit features)
- `STELLCODEX_S3_ENDPOINT_URL`
- `STELLCODEX_S3_BUCKET`
- `STELLCODEX_S3_ACCESS_KEY_ID`
- `STELLCODEX_S3_SECRET_ACCESS_KEY`
- `SITE_URL`

## 3) Install command
From repo root:
```bash
cd backend
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 4) Migration command
From `backend/`:
```bash
alembic upgrade head
```

## 5) Start command
From `backend/`:
```bash
uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

## 6) Health verification command
```bash
curl -fsS http://127.0.0.1:${PORT:-8000}/api/v1/health
```

Also verify docs and OpenAPI:
```bash
curl -I http://127.0.0.1:${PORT:-8000}/docs
curl -fsS http://127.0.0.1:${PORT:-8000}/openapi.json | head -c 200
```

## 7) Common failure classes + exact fixes
1. **`DATABASE_URL` missing/invalid scheme**
   - Fix: set `DATABASE_URL=postgresql+psycopg2://...`.
2. **JWT secret validation error**
   - Fix: set `JWT_SECRET` (min 32 chars).
3. **`ModuleNotFoundError` after fresh build**
   - Fix: reinstall exactly from `backend/requirements.txt`; do not install ad-hoc packages.
4. **Migration mismatch**
   - Fix: run `alembic upgrade head` before app start.
5. **Wrong deploy root on Render**
   - Fix: set service Root Directory to `backend`.

## 8) Server rebuild procedure (disposable runtime)
1. Provision server/runtime.
2. Checkout repository.
3. Inject env contract (`DATABASE_URL`, `JWT_SECRET`, production vars).
4. `cd backend && pip install -r requirements.txt`.
5. `alembic upgrade head`.
6. Start `uvicorn app.main:app ...`.
7. Run health/docs/openapi checks.

## 9) Render-specific notes
- **Root Directory:** `backend`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Render runtime pin comes from `backend/runtime.txt`.
- Keep env var names exactly as in section 2.

## 10) “New runtime in 15 minutes” recovery checklist
- [ ] Repo cloned and on correct branch/commit
- [ ] Runtime is Python 3.11.9
- [ ] `DATABASE_URL` + `JWT_SECRET` injected
- [ ] `pip install -r backend/requirements.txt` passes
- [ ] `alembic upgrade head` passes
- [ ] Uvicorn starts cleanly
- [ ] `/api/v1/health` returns 200
- [ ] `/docs` returns 200/HTML
- [ ] `/openapi.json` returns valid JSON with critical route groups

## Evidence artifacts in repo
- Dependency manifest: `backend/requirements.txt`
- Startup import audit output: `docs/STARTUP_IMPORT_AUDIT.txt`
- Env contract + deploy checklist: this document
- Cold-boot verification helper: `backend/scripts/cold_boot_verify.sh`
