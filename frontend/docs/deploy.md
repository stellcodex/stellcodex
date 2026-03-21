# STELLCODEX Frontend Deploy (Vercel)

## Framework
- Next.js (App Router)

## Route List (primary UX)
- `/`
- `/share`
- `/share/file/:id`
- `/view`
- `/view/file/:id`
- `/mold`
- `/s/:token`
- `/admin`
- `/admin/job/:id`

## Build
- Install: `npm install`
- Build: `npm run build`
- Start (local): `npm run start`
- Output: Next.js server output (Vercel detects automatically)

## Node
- `>=20.18.0 <23`

## Vercel Settings
1. Root Directory = `frontend`
2. Framework Preset = `Next.js`
3. Install Command = `npm install`
4. Build Command = `npm run build`
5. Output = `Next.js (auto)`
3. Env vars:
   - `NEXT_PUBLIC_API_URL=/api/v1`
   - `NEXT_PUBLIC_API_BASE=/api/v1` (optional legacy alias)
   - `BACKEND_API_ORIGIN=http://127.0.0.1:18000`
   - `INTERNAL_FRONTEND_ORIGIN=http://127.0.0.1:3010`
   - `AUTH_SESSION_COOKIE_NAME=stellcodex_session`
   - `STELLCODEX_ENABLE_MOCK_ADMIN=0`
   - `DATABASE_URL=postgresql://USER:PASSWORD@POOLED_HOST/neondb?sslmode=require&schema=stellcodex_prod&options=endpoint%3DNEON_ENDPOINT`
   - `DIRECT_URL=postgresql://USER:PASSWORD@DIRECT_HOST/neondb?sslmode=require&schema=stellcodex_prod&options=endpoint%3DNEON_ENDPOINT`

## PROD Schema MUST Be Fixed
- Production schema must be a fixed name: `stellcodex_prod`
- Runtime uses `DATABASE_URL` (pooled Neon)
- Migration deploy uses `DIRECT_URL` (direct Neon)
- Local/smoke runs may use timestamp schemas (ephemeral)

Schema examples (Neon):
- Method A (query param):
  - `...?...sslmode=require&schema=stellcodex_prod&options=endpoint%3DNEON_ENDPOINT`
- Method B (search_path in options):
  - `...?...sslmode=require&options=endpoint%3DNEON_ENDPOINT%20-c%20search_path%3Dstellcodex_prod`

## Notes
- This patch completes Share/View/Mold/Home UI with mock Next API routes for deterministic UX.
- Route hygiene is enforced by middleware allowlist. Legacy routes stay in repo but return `404` at runtime.
- Browser requests stay same-origin on `/api/v1`; internal server-side fetches use `BACKEND_API_ORIGIN`.
- Build runs `node scripts/prisma-safe.cjs && next build` so Prisma generate is skipped only when packages/env are missing.

## Rollback (Vercel)
1. Vercel Dashboard -> Project -> `Deployments`
2. Open the previous successful deployment
3. Click `Promote to Production` (or equivalent)
4. If DNS is unchanged, rollback is effective immediately after promotion
