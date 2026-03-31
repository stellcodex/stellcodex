#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

: "${DATABASE_URL:?DATABASE_URL is required}"
: "${JWT_SECRET:?JWT_SECRET is required}"

if [[ "${STATIC_OPENAPI_ONLY:-0}" == "1" ]]; then
  PYTHONPATH=. python - <<'PY'
from app.main import app
spec = app.openapi()
paths = spec.get("paths", {})
required_groups = [
    "/api/v1/files",
    "/api/v1/jobs",
    "/api/v1/orchestrator",
    "/api/v1/admin",
    "/api/v1/quotes",
    "/api/v1/stell-ai",
    "/api/v1/ai",
]
missing = [g for g in required_groups if not any(p.startswith(g) for p in paths)]
if missing:
    raise SystemExit(f"Missing route groups in OpenAPI: {missing}")
print("STATIC_OPENAPI_VERIFY_OK")
PY
  exit 0
fi

if [[ "${SKIP_INSTALL:-0}" != "1" ]]; then
  python -m pip install -r requirements.txt
fi

if [[ "${SKIP_MIGRATIONS:-0}" != "1" ]]; then
  alembic upgrade head
fi

PORT="${PORT:-8000}"
uvicorn app.main:app --host 127.0.0.1 --port "$PORT" >/tmp/stellcodex_uvicorn.log 2>&1 &
UVICORN_PID=$!
trap 'kill ${UVICORN_PID} >/dev/null 2>&1 || true' EXIT

for _ in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${PORT}/api/v1/health" >/tmp/stellcodex_health.json; then
    break
  fi
  sleep 1
done

curl -fsS "http://127.0.0.1:${PORT}/openapi.json" >/tmp/stellcodex_openapi.json
curl -I "http://127.0.0.1:${PORT}/docs" >/tmp/stellcodex_docs.headers

python - <<'PY'
import json
from pathlib import Path
spec = json.loads(Path('/tmp/stellcodex_openapi.json').read_text())
paths = spec.get('paths', {})
required_groups = [
    '/api/v1/files',
    '/api/v1/jobs',
    '/api/v1/orchestrator',
    '/api/v1/admin',
    '/api/v1/quotes',
    '/api/v1/stell-ai',
    '/api/v1/ai',
]
missing = []
for group in required_groups:
    if not any(p.startswith(group) for p in paths):
        missing.append(group)
if missing:
    raise SystemExit(f"Missing route groups in OpenAPI: {missing}")
print('OPENAPI_ROUTE_GROUPS_OK')
PY

echo "COLD_BOOT_VERIFY_OK"
