# STELLCODEX Release Checklist

- Frontend build
  - `cd frontend && npm run build`
- Backend unittest
  - `cd /var/www/stellcodex && python3 -m unittest -q backend/tests/test_hybrid_v1_geometry_merge_policy.py`
- Smoke gate
  - `cd /var/www/stellcodex && ./scripts/smoke.sh`
- Nginx syntax
  - `nginx -t`
- Container health
  - `docker ps --format "table {{.Names}}\t{{.Status}}"`
- Health endpoints
  - `curl -sS http://127.0.0.1:8000/api/v1/health`
  - `curl -I -sS http://127.0.0.1:3000/`
- Log tail
  - `docker logs --tail 120 stellcodex-backend`
  - `docker logs --tail 120 stellcodex-worker`
