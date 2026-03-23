# STELLCODEX Frontend

This frontend is the STELLCODEX product shell. It serves the public site, authenticated workspace, viewer, share surface, and admin shell.

## Runtime Rules

- public entry is nginx on `80/443`
- browser API base is `NEXT_PUBLIC_API_BASE_URL=/api/v1`
- backend authority stays behind nginx; the frontend must not hard-code side ports
- `BACKEND_API_ORIGIN` is optional and only for local development without nginx

## Local Development

```bash
npm ci
NEXT_PUBLIC_API_BASE_URL=/api/v1 BACKEND_API_ORIGIN=http://127.0.0.1:8000 npm run dev
```

The canonical production frontend port is `3010`, but it is expected to sit behind nginx rather than be exposed directly.
