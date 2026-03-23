# STELLCODEX Release Gate (Frontend)

## Before Deploy
- `NEXT_PUBLIC_API_BASE_URL=/api/v1`
- nginx points `/` to `127.0.0.1:3010`
- nginx points `/api/` to `127.0.0.1:8000`
- no Vercel deployment path is active

## Local Release Gate Script
```bash
bash frontend/scripts/release-gate.sh
```

What it checks:
- build (`npm run build`)
- local server boot (`next start`)
- route allowlist smoke (`/`, `/share`, `/view`, `/admin`, `/api/*`, `/robots.txt`)
- `_next` asset fetch (build artifact served)

## After Deploy (Production URL Smoke)
- `GET /` -> `200`
- `GET /share` -> `200` (or controlled redirect)
- `GET /view` -> `200` (or controlled redirect)
- `GET /mold` -> `200`
- `GET /s/<token>` -> `200` or `404` (validity-dependent, but route not blocked)
- `GET /admin` -> `302/401/200` (not `404`)
- `GET /robots.txt` -> `200`

## Rollback
1. Rebuild the previous GitHub commit with `docker compose -f infrastructure/deploy/docker-compose.yml build frontend`
2. Recreate the frontend container
3. Verify nginx still routes `/_next/` and `/` to `127.0.0.1:3010`
