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
3. Env vars:
   - `NEXT_PUBLIC_API_URL=https://api.stellcodex.com`
   - `DATABASE_URL=<Neon URL>`
   - `DIRECT_URL=<Neon URL>` (recommended for Prisma)

## Notes
- This patch completes Share/View/Mold/Home UI with mock Next API routes for deterministic UX.
- Existing backend client (`NEXT_PUBLIC_API_URL`) remains in project for backend-origin calls.
- When Prisma packages are installed, build/postinstall auto-runs `prisma generate`.

