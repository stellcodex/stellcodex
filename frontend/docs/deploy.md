# STELLCODEX Frontend Deploy

## Canonical Production Path

- build source: `frontend/Dockerfile`
- runtime port: `127.0.0.1:3010`
- public entry: nginx `infrastructure/nginx/stellcodex.conf`
- browser API base: `NEXT_PUBLIC_API_BASE_URL=/api/v1`

## Build And Run

```bash
docker compose -f infrastructure/deploy/docker-compose.yml build frontend
docker compose -f infrastructure/deploy/docker-compose.yml up -d frontend
```

## Runtime Rules

- the frontend is not a public edge service; nginx is
- browser requests must stay same-origin on `/api/v1`
- `BACKEND_API_ORIGIN` is optional and only for local development without nginx
- Vercel is not part of the canonical deployment path
