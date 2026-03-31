# Backend Environment Contract Summary

## Strictly required for API boot
- `DATABASE_URL` (PostgreSQL URL, required)
- `JWT_SECRET` (or `SECRET_KEY` / `APP_SECRET` / `SIGNING_KEY`, required, min length 32)

## Required for full production capability (non-boot-critical)
- `REDIS_URL` (queues, rate limiting, background jobs)
- `STELLCODEX_S3_ENDPOINT_URL`, `STELLCODEX_S3_BUCKET`, `STELLCODEX_S3_ACCESS_KEY_ID`, `STELLCODEX_S3_SECRET_ACCESS_KEY` (object storage)
- OAuth vars if Google login is enabled: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REDIRECT_URI`

## Security hardening retained
- Missing JWT secret fails fast.
- Missing or non-PostgreSQL database URL fails fast.
