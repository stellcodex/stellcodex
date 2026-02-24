# Neon + Prisma Migration (STELLCODEX UI)

## 1) Env (Neon)
Use Neon connection strings with `sslmode=require` and endpoint option:

```env
DATABASE_URL=postgresql://USER:PASS@POOLED_HOST/neondb?sslmode=require&options=endpoint%3D<endpoint>
DIRECT_URL=postgresql://USER:PASS@DIRECT_HOST/neondb?sslmode=require&options=endpoint%3D<endpoint>
STELLCODEX_ENABLE_MOCK_ADMIN=1   # local demo
STELLCODEX_ENABLE_MOCK_ADMIN=0   # production
NEXT_PUBLIC_API_URL=https://api.stellcodex.com
NEXT_PUBLIC_API_BASE=https://api.stellcodex.com   # optional legacy alias
```

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
npm run prisma:seed
```

## 5) Seed Produces
- Project: `Genel`
- System folders: 3D Modeller, 2D Çizimler, Dokümanlar, Görseller, Arşiv
- Sample files for 3D/2D/PDF/Image/ZIP
- Sample jobs for `ready`, `preview`, `security`, `NEEDS_APPROVAL`
- Public share token: `demo-share-token`

## 6) Storage Note
- Current implementation uses metadata + placeholder previews for UI completion.
- Next phase: bind `storageKey` to MinIO/S3/R2 and keep Prisma as metadata source.
