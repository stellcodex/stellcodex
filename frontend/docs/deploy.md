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
   - `NEXT_PUBLIC_API_URL=https://api.stellcodex.com`
   - `NEXT_PUBLIC_API_BASE=https://api.stellcodex.com` (optional legacy alias)
   - `STELLCODEX_ENABLE_MOCK_ADMIN=0`
   - `DATABASE_URL=postgresql://USER:PASSWORD@POOLED_HOST/neondb?sslmode=require&options=endpoint%3DNEON_ENDPOINT`
   - `DIRECT_URL=postgresql://USER:PASSWORD@DIRECT_HOST/neondb?sslmode=require&options=endpoint%3DNEON_ENDPOINT`

## Notes
- This patch completes Share/View/Mold/Home UI with mock Next API routes for deterministic UX.
- Route hygiene is enforced by middleware allowlist. Legacy routes stay in repo but return `404` at runtime.
- Existing backend client uses `NEXT_PUBLIC_API_URL` (and middleware also supports optional `NEXT_PUBLIC_API_BASE` alias).
- Build runs `node scripts/prisma-safe.cjs && next build` so Prisma generate is skipped only when packages/env are missing.
