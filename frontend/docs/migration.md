# Neon + Prisma Migration (STELLCODEX UI)

## 1) Env (Neon)
Use Neon connection strings with `sslmode=require` and endpoint option:

```env
DATABASE_URL=postgresql://USER:PASS@POOLED_HOST/neondb?sslmode=require&schema=stellcodex_prod&options=endpoint%3D<endpoint>
DIRECT_URL=postgresql://USER:PASS@DIRECT_HOST/neondb?sslmode=require&schema=stellcodex_prod&options=endpoint%3D<endpoint>
STELLCODEX_ENABLE_MOCK_ADMIN=1   # local demo
STELLCODEX_ENABLE_MOCK_ADMIN=0   # production
NEXT_PUBLIC_API_URL=/api/v1
NEXT_PUBLIC_API_BASE=/api/v1   # optional legacy alias
BACKEND_API_ORIGIN=http://127.0.0.1:18000
INTERNAL_FRONTEND_ORIGIN=http://127.0.0.1:3010
AUTH_SESSION_COOKIE_NAME=stellcodex_session
```

## PROD Schema MUST Be Fixed
- PROD must use a fixed schema name: `stellcodex_prod`
- SMOKE/LOCAL may use timestamp schemas (ephemeral), e.g. `stellcodex_ui_smoke_<timestamp>`
- `prisma migrate deploy` should use `DIRECT_URL`
- App runtime should use `DATABASE_URL`

Alternative Neon schema encoding:
- Method A (query param): `...&schema=stellcodex_prod&options=endpoint%3D<endpoint>`
- Method B (search_path via options): `...&options=endpoint%3D<endpoint>%20-c%20search_path%3Dstellcodex_prod`

## 2) Install Prisma (if missing)
```bash
npm i @prisma/client
npm i -D prisma
```

## 3) Local (dev) Generate / Migrate / Seed
```bash
npm run prisma:generate
npm run prisma:migrate:dev -- --name init
npm run prisma:seed
```

## 4) Production Deploy Migration / Seed
```bash
npm run prisma:generate
npm run prisma:migrate:deploy
ALLOW_PROD_SEED=1 npm run prisma:seed
# or
npm run prisma:seed:prod
```

Seed guard note:
- `prisma/seed.js` refuses to run in `NODE_ENV=production` unless `ALLOW_PROD_SEED=1`

## 5) Seed Produces
- Project: `Genel`
- System folders: 3D Modeller, 2D Çizimler, Dokümanlar, Görseller, Arşiv
- Sample files for 3D/2D/PDF/Image/ZIP
- Sample jobs for `ready`, `preview`, `security`, `NEEDS_APPROVAL`
- Public share token: `demo-share-token`

## 6) Storage Note
- Current implementation uses metadata + placeholder previews for UI completion.
- Next phase: bind `storageKey` to MinIO/S3/R2 and keep Prisma as metadata source.
