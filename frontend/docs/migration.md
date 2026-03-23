# Frontend Migration Notes

The frontend no longer carries a Vercel/Neon deployment contract. The canonical production model is Dockerized Next.js behind nginx with browser API traffic on `/api/v1`.

Use these settings for local development:

```env
NEXT_PUBLIC_API_BASE_URL=/api/v1
BACKEND_API_ORIGIN=http://127.0.0.1:8000
INTERNAL_FRONTEND_ORIGIN=http://127.0.0.1:3010
AUTH_SESSION_COOKIE_NAME=stellcodex_session
```

Prisma tasks remain local-development concerns only. Production runtime is defined by `frontend/Dockerfile` and `infrastructure/deploy/docker-compose.yml`.
