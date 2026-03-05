# FINAL SHIP BASELINE

Generated: 2026-03-05T12:39:55+03:00

## 1) System baseline artifacts

- `/var/www/stellcodex/_reports/FINAL_SHIP/SYSTEM_BASELINE_20260305_123955.txt`
  - Includes: `date`, `git rev-parse --short HEAD`, `pm2 list`, `docker ps`, `curl -i http://localhost:3100`
  - Result highlights:
    - PM2: `stellcodex-next` + `stellcodex-next-3100` online
    - Docker: `stellcodex-backend`, `stellcodex-worker`, `stellcodex-redis`, `stellcodex-postgres`, `stellcodex-minio` up/healthy
    - `curl -i http://localhost:3100` => `HTTP/1.1 200 OK`

## 2) Redirect source scan artifacts

- `/var/www/stellcodex/_reports/FINAL_SHIP/REDIRECT_SCAN_20260305_120200.txt`
  - Includes:
    - `rg -n "NextResponse\.(redirect|rewrite)|/workspace|session_" frontend/src frontend/src/middleware.ts || true`
    - `rg -n "router\.push|redirect\(|/workspace|session_" frontend/src || true`
    - `nginx -T | rg -n "rewrite|location /|/workspace|return 30" || true`

## 3) Routing contract proof

- `/var/www/stellcodex/_reports/FINAL_SHIP/ROUTING_CONTRACT_PROOF.txt`
  - `/` on 3000 => `200`, landing marker present, no redirect to `/workspace/session_*`
  - `/workspace` on 3000 => renders `Workspace hazirlaniyor...` then client redirect contract
  - Deep-link sample (`/workspace/<id>/files`) returns workspace page markers
  - Required check: `/` on 3100 => `200`

## Findings

- Forced root redirect removed from frontend root page.
- Routing contract now holds:
  - `GET /` => landing dashboard
  - `GET /workspace` => session bootstrap page (`WorkspaceRedirect`) with client-side create/resume
  - `GET /workspace/session_*` => deep links active
- Frontend canonical proxy is active for `/api/v1` on both 3000 and 3100:
  - `/var/www/stellcodex/_reports/FINAL_SHIP/FRONTEND_PROXY_PROOF.txt`
