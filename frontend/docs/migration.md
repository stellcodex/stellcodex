# Neon + Prisma Migration (STELLCODEX UI)

## 1) Env
Use Neon connection string with endpoint option:

```env
DATABASE_URL=postgresql://USER:PASS@HOST/neondb?sslmode=require&options=endpoint%3D<endpoint>
DIRECT_URL=postgresql://USER:PASS@HOST/neondb?sslmode=require&options=endpoint%3D<endpoint>
```

## 2) Install Prisma (if missing)
```bash
npm install prisma @prisma/client
```

## 3) Generate / Migrate / Seed
```bash
npx prisma generate
npx prisma migrate dev --name init_stellcodex_ui
npx prisma db seed
```

Production:
```bash
npx prisma migrate deploy
npx prisma db seed
```

## 4) Seed Produces
- Project: `Genel`
- System folders: 3D Modeller, 2D Çizimler, Dokümanlar, Görseller, Arşiv
- Sample files for 3D/2D/PDF/Image/ZIP
- Sample jobs for `ready`, `preview`, `security`, `NEEDS_APPROVAL`
- Public share token: `demo-share-token`

## 5) Storage Note
- Current implementation uses metadata + placeholder previews for UI completion.
- Next phase: bind `storageKey` to MinIO/S3/R2 and keep Prisma as metadata source.

