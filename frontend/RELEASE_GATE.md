# STELLCODEX Release Gate (Frontend)

## Before Deploy (Vercel Env Checklist)
- `NEXT_PUBLIC_API_URL=https://api.stellcodex.com`
- `NEXT_PUBLIC_API_BASE=https://api.stellcodex.com` (optional legacy alias)
- `STELLCODEX_ENABLE_MOCK_ADMIN=0`
- `DATABASE_URL=<Neon pooled runtime URL>`
- `DIRECT_URL=<Neon direct migrate URL>`
- PROD schema MUST be fixed:
  - `schema=stellcodex_prod` (query param) OR
  - `search_path=stellcodex_prod` via `options`

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

## Rollback (Vercel)
1. Vercel Dashboard -> Project -> `Deployments`
2. Open previous known-good deployment
3. Click `Promote to Production` (or equivalent redeploy/promote action)
4. DNS stays the same, rollback is immediate once promotion completes

