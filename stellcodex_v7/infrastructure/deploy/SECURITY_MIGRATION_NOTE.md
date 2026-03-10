# Security Migration Note (V7)

This patch removes hardcoded `minioadmin/minioadmin` credentials from
`infrastructure/deploy/docker-compose.local.yml`.

## Required Environment Variables

Set these before running `docker compose`:

- `STELLCODEX_S3_ACCESS_KEY_ID`
- `STELLCODEX_S3_SECRET_ACCESS_KEY`

`docker-compose.local.yml` now fails fast if these values are not provided.

## Rotation Procedure

1. Generate new random MinIO credentials.
2. Update `.env` (or deployment secret store) with new values.
3. Restart stack (`docker compose down && docker compose up -d --build`).
4. Verify backend and worker both read the same new credential pair.
5. Run `infrastructure/deploy/scripts/release_gate_v7.sh` and keep evidence bundle.
