#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EVIDENCE_DIR="${ROOT_DIR}/evidence"
OUT_FILE="${EVIDENCE_DIR}/runtime_restore_probe_output.txt"
BACKUP_DIR="${BACKUP_DIR:-${ROOT_DIR}/backups}"
MIRROR_ROOT="${MIRROR_ROOT:-${ROOT_DIR}/backups/object_mirror}"
DB_CONTAINER="${DB_CONTAINER:-deploy_postgres_1}"
DB_USER="${DB_USER:-stellcodex}"
DB_NAME="${DB_NAME:-stellcodex}"
RESTORE_DB_NAME="${RESTORE_DB_NAME:-stellcodex_restore_runtime_probe}"
PROBE_NETWORK="${PROBE_NETWORK:-deploy_default}"
PROBE_BACKEND_NAME="${PROBE_BACKEND_NAME:-restore_backend_probe}"
PROBE_WORKER_NAME="${PROBE_WORKER_NAME:-restore_worker_probe}"
PROBE_REDIS_NAME="${PROBE_REDIS_NAME:-restore_redis_probe}"
PROBE_MINIO_NAME="${PROBE_MINIO_NAME:-restore_minio_probe}"
PROBE_REDIS_HOST="${PROBE_REDIS_HOST:-restore-redis-probe}"
PROBE_MINIO_HOST="${PROBE_MINIO_HOST:-restore-minio-probe}"
PROBE_BACKEND_PORT="${PROBE_BACKEND_PORT:-18180}"
PROBE_MINIO_PORT="${PROBE_MINIO_PORT:-19110}"
PROBE_ACCESS_KEY="${PROBE_ACCESS_KEY:-stellcodex}"
PROBE_SECRET_KEY="${PROBE_SECRET_KEY:-stellcodex123}"
STEP_SAMPLE="${STEP_SAMPLE:-/var/stellcodex/work/samples/parca.STEP}"
DUMP_FILE="${DUMP_FILE:-}"
KEEP_RESTORE_DB="${KEEP_RESTORE_DB:-0}"
KEEP_PROBE_CONTAINERS="${KEEP_PROBE_CONTAINERS:-0}"
KEEP_PROBE_DATA="${KEEP_PROBE_DATA:-0}"
LIVE_BACKEND_CONTAINER="${LIVE_BACKEND_CONTAINER:-deploy_backend_1}"
LIVE_WORKER_CONTAINER="${LIVE_WORKER_CONTAINER:-deploy_worker_1}"
LIVE_MINIO_CONTAINER="${LIVE_MINIO_CONTAINER:-deploy_minio_1}"

mkdir -p "${EVIDENCE_DIR}"
exec > >(tee "${OUT_FILE}") 2>&1

PROBE_MINIO_DATA_ROOT=""
PROBE_WORK_ROOT=""

fail() {
  echo "[FAIL] $1"
  collect_logs
  echo "RESULT=FAIL"
  echo "EVIDENCE=${OUT_FILE}"
  exit 1
}

pass() {
  echo "[PASS] $1"
}

collect_logs() {
  docker logs "${PROBE_BACKEND_NAME}" > "${EVIDENCE_DIR}/runtime_restore_probe_backend.log" 2>&1 || true
  docker logs "${PROBE_WORKER_NAME}" > "${EVIDENCE_DIR}/runtime_restore_probe_worker.log" 2>&1 || true
  docker logs "${PROBE_MINIO_NAME}" > "${EVIDENCE_DIR}/runtime_restore_probe_minio.log" 2>&1 || true
  docker logs "${PROBE_REDIS_NAME}" > "${EVIDENCE_DIR}/runtime_restore_probe_redis.log" 2>&1 || true
}

cleanup() {
  collect_logs
  if [[ "${KEEP_PROBE_CONTAINERS}" != "1" ]]; then
    docker rm -f "${PROBE_BACKEND_NAME}" "${PROBE_WORKER_NAME}" "${PROBE_MINIO_NAME}" "${PROBE_REDIS_NAME}" >/dev/null 2>&1 || true
  fi
  if [[ "${KEEP_RESTORE_DB}" != "1" ]]; then
    docker exec "${DB_CONTAINER}" sh -lc \
      "export PGPASSWORD=\"\${PGPASSWORD:-\${POSTGRES_PASSWORD:-}}\"; dropdb --if-exists -U \"${DB_USER}\" \"${RESTORE_DB_NAME}\"" >/dev/null 2>&1 || true
  fi
  if [[ "${KEEP_PROBE_DATA}" != "1" ]]; then
    [[ -n "${PROBE_MINIO_DATA_ROOT}" && -d "${PROBE_MINIO_DATA_ROOT}" ]] && rm -rf "${PROBE_MINIO_DATA_ROOT}"
    [[ -n "${PROBE_WORK_ROOT}" && -d "${PROBE_WORK_ROOT}" ]] && rm -rf "${PROBE_WORK_ROOT}"
  fi
}

trap cleanup EXIT

pick_port() {
  local default_port="$1"
  shift
  local candidate
  for candidate in "${default_port}" "$@"; do
    if ! ss -ltn "( sport = :${candidate} )" 2>/dev/null | tail -n +2 | grep -q .; then
      echo "${candidate}"
      return 0
    fi
  done
  return 1
}

find_latest_dump() {
  find "${BACKUP_DIR}" -maxdepth 1 -type f -name "db_${DB_NAME}_*.sql.gz" | sort | tail -n 1
}

parse_json_field() {
  local file="$1"
  local field="$2"
  python3 - <<PY
import json
try:
    data = json.load(open("${file}"))
except Exception:
    data = {}
value = data.get("${field}", "")
print(value if value is not None else "")
PY
}

echo "# Runtime restore probe"
date -Iseconds
echo "db_container=${DB_CONTAINER}"
echo "restore_db_name=${RESTORE_DB_NAME}"
echo "probe_network=${PROBE_NETWORK}"

command -v docker >/dev/null 2>&1 || fail "docker is required"
command -v curl >/dev/null 2>&1 || fail "curl is required"
command -v ss >/dev/null 2>&1 || fail "ss is required"
[[ -f "${STEP_SAMPLE}" ]] || fail "step sample missing: ${STEP_SAMPLE}"
[[ -d "${MIRROR_ROOT}/${DB_NAME}" || -d "${MIRROR_ROOT}/stellcodex" ]] || true
[[ -d "${MIRROR_ROOT}/stellcodex" ]] || fail "object mirror missing: ${MIRROR_ROOT}/stellcodex"

docker inspect "${DB_CONTAINER}" >/dev/null 2>&1 || fail "db container not found: ${DB_CONTAINER}"
docker inspect "${LIVE_BACKEND_CONTAINER}" >/dev/null 2>&1 || fail "live backend container not found: ${LIVE_BACKEND_CONTAINER}"
docker inspect "${LIVE_WORKER_CONTAINER}" >/dev/null 2>&1 || fail "live worker container not found: ${LIVE_WORKER_CONTAINER}"
docker inspect "${LIVE_MINIO_CONTAINER}" >/dev/null 2>&1 || fail "live minio container not found: ${LIVE_MINIO_CONTAINER}"

BACKEND_IMAGE="$(docker inspect "${LIVE_BACKEND_CONTAINER}" --format '{{.Image}}')"
WORKER_IMAGE="$(docker inspect "${LIVE_WORKER_CONTAINER}" --format '{{.Image}}')"
MINIO_IMAGE="$(docker inspect "${LIVE_MINIO_CONTAINER}" --format '{{.Config.Image}}')"
REDIS_IMAGE="redis:7"

PROBE_BACKEND_PORT="$(pick_port "${PROBE_BACKEND_PORT}" 18181 18182 18183 18184 18185)" || fail "no free backend probe port"
PROBE_MINIO_PORT="$(pick_port "${PROBE_MINIO_PORT}" 19111 19112 19113 19114 19115)" || fail "no free minio probe port"
echo "probe_backend_port=${PROBE_BACKEND_PORT}"
echo "probe_minio_port=${PROBE_MINIO_PORT}"

PROBE_MINIO_DATA_ROOT="$(mktemp -d /tmp/runtime-restore-minio-XXXXXX)"
PROBE_WORK_ROOT="$(mktemp -d /tmp/runtime-restore-work-XXXXXX)"
cp -r "${MIRROR_ROOT}/stellcodex" "${PROBE_MINIO_DATA_ROOT}/"
pass "probe object data copied to ${PROBE_MINIO_DATA_ROOT}"

if [[ -z "${DUMP_FILE}" ]]; then
  DUMP_FILE="$(find_latest_dump)"
fi
[[ -n "${DUMP_FILE}" ]] || fail "no dump found in ${BACKUP_DIR}"
[[ -f "${DUMP_FILE}" ]] || fail "dump file missing: ${DUMP_FILE}"
pass "selected dump ${DUMP_FILE}"

echo "[1/7] recreate restore database"
docker exec "${DB_CONTAINER}" sh -lc \
  "export PGPASSWORD=\"\${PGPASSWORD:-\${POSTGRES_PASSWORD:-}}\"; dropdb --if-exists -U \"${DB_USER}\" \"${RESTORE_DB_NAME}\" && createdb -U \"${DB_USER}\" \"${RESTORE_DB_NAME}\"" \
  || fail "failed to recreate restore database"
pass "restore database recreated"

echo "[2/7] restore dump into runtime probe database"
gzip -dc "${DUMP_FILE}" | docker exec -i "${DB_CONTAINER}" sh -lc \
  "export PGPASSWORD=\"\${PGPASSWORD:-\${POSTGRES_PASSWORD:-}}\"; psql -v ON_ERROR_STOP=1 -U \"${DB_USER}\" -d \"${RESTORE_DB_NAME}\"" \
  >/dev/null || fail "restore into ${RESTORE_DB_NAME} failed"
pass "dump restored"

echo "[3/7] start isolated redis + minio"
docker rm -f "${PROBE_REDIS_NAME}" "${PROBE_MINIO_NAME}" >/dev/null 2>&1 || true
docker run -d --rm \
  --name "${PROBE_REDIS_NAME}" \
  --network "${PROBE_NETWORK}" \
  --network-alias "${PROBE_REDIS_HOST}" \
  "${REDIS_IMAGE}" >/dev/null || fail "failed to start redis probe"

docker run -d --rm \
  --name "${PROBE_MINIO_NAME}" \
  --network "${PROBE_NETWORK}" \
  --network-alias "${PROBE_MINIO_HOST}" \
  -p "127.0.0.1:${PROBE_MINIO_PORT}:9000" \
  -e MINIO_ROOT_USER="${PROBE_ACCESS_KEY}" \
  -e MINIO_ROOT_PASSWORD="${PROBE_SECRET_KEY}" \
  -v "${PROBE_MINIO_DATA_ROOT}:/data" \
  "${MINIO_IMAGE}" server /data >/dev/null || fail "failed to start minio probe"

for _ in $(seq 1 30); do
  if docker exec "${PROBE_REDIS_NAME}" redis-cli ping >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
docker exec "${PROBE_REDIS_NAME}" redis-cli ping >/dev/null 2>&1 || fail "redis probe health failed"

for _ in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${PROBE_MINIO_PORT}/minio/health/live" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
curl -fsS "http://127.0.0.1:${PROBE_MINIO_PORT}/minio/health/live" >/dev/null 2>&1 || fail "minio probe health failed"
pass "redis and minio probes live"

echo "[4/7] start isolated backend + worker"
docker rm -f "${PROBE_BACKEND_NAME}" "${PROBE_WORKER_NAME}" >/dev/null 2>&1 || true
docker run -d --rm \
  --name "${PROBE_BACKEND_NAME}" \
  --network "${PROBE_NETWORK}" \
  -p "127.0.0.1:${PROBE_BACKEND_PORT}:8000" \
  -v /root/workspace/backend:/app \
  -v "${PROBE_WORK_ROOT}:/tmp/stellcodex/work" \
  -e DATABASE_URL="postgresql+psycopg2://stellcodex:stellcodex@postgres:5432/${RESTORE_DB_NAME}" \
  -e REDIS_URL="redis://${PROBE_REDIS_HOST}:6379/0" \
  -e STELLCODEX_S3_ENDPOINT_URL="http://${PROBE_MINIO_HOST}:9000" \
  -e STELLCODEX_S3_REGION="us-east-1" \
  -e STELLCODEX_S3_BUCKET="stellcodex" \
  -e STELLCODEX_S3_ACCESS_KEY_ID="${PROBE_ACCESS_KEY}" \
  -e STELLCODEX_S3_SECRET_ACCESS_KEY="${PROBE_SECRET_KEY}" \
  -e PUBLIC_S3_BASE_URL="http://127.0.0.1:${PROBE_MINIO_PORT}" \
  -e JWT_SECRET="9d9f63a2f29f46025b3da7cb7c33f0431981fba0a7f113f96eeea69f6fd7932c" \
  -e JWT_ALG="HS256" \
  -e ACCESS_TOKEN_MINUTES="30" \
  -e REFRESH_TOKEN_DAYS="14" \
  -e FEATURE_FILES="true" \
  -e MAX_UPLOAD_BYTES="209715200" \
  -e ALLOWED_CONTENT_TYPES="model/stl,model/step,model/iges,application/step,application/iges,application/pdf,image/png,image/jpeg,model/gltf-binary,model/gltf+json,application/octet-stream,text/plain" \
  -e CONVERSION_TIMEOUT_SECONDS="1800" \
  -e BLENDER_TIMEOUT_SECONDS="600" \
  -e WORKDIR="/tmp/stellcodex/work" \
  -e PYTHONUNBUFFERED="1" \
  "${BACKEND_IMAGE}" \
  sh -lc "until nc -z postgres 5432; do sleep 1; done; until nc -z ${PROBE_MINIO_HOST} 9000; do sleep 1; done; until nc -z ${PROBE_REDIS_HOST} 6379; do sleep 1; done; uvicorn app.main:app --host 0.0.0.0 --port 8000" \
  >/dev/null || fail "failed to start backend probe"

docker run -d --rm \
  --name "${PROBE_WORKER_NAME}" \
  --network "${PROBE_NETWORK}" \
  -v /root/workspace/backend:/app \
  -v "${PROBE_WORK_ROOT}:/tmp/stellcodex/work" \
  -e DATABASE_URL="postgresql+psycopg2://stellcodex:stellcodex@postgres:5432/${RESTORE_DB_NAME}" \
  -e REDIS_URL="redis://${PROBE_REDIS_HOST}:6379/0" \
  -e STELLCODEX_S3_ENDPOINT_URL="http://${PROBE_MINIO_HOST}:9000" \
  -e STELLCODEX_S3_REGION="us-east-1" \
  -e STELLCODEX_S3_BUCKET="stellcodex" \
  -e STELLCODEX_S3_ACCESS_KEY_ID="${PROBE_ACCESS_KEY}" \
  -e STELLCODEX_S3_SECRET_ACCESS_KEY="${PROBE_SECRET_KEY}" \
  -e PUBLIC_S3_BASE_URL="http://127.0.0.1:${PROBE_MINIO_PORT}" \
  -e JWT_SECRET="9d9f63a2f29f46025b3da7cb7c33f0431981fba0a7f113f96eeea69f6fd7932c" \
  -e JWT_ALG="HS256" \
  -e ACCESS_TOKEN_MINUTES="30" \
  -e REFRESH_TOKEN_DAYS="14" \
  -e FEATURE_FILES="true" \
  -e MAX_UPLOAD_BYTES="209715200" \
  -e ALLOWED_CONTENT_TYPES="model/stl,model/step,model/iges,application/step,application/iges,application/pdf,image/png,image/jpeg,model/gltf-binary,model/gltf+json,application/octet-stream,text/plain" \
  -e CONVERSION_TIMEOUT_SECONDS="1800" \
  -e BLENDER_TIMEOUT_SECONDS="600" \
  -e WORKDIR="/tmp/stellcodex/work" \
  -e PYTHONUNBUFFERED="1" \
  "${WORKER_IMAGE}" \
  sh -lc "until nc -z postgres 5432; do sleep 1; done; until nc -z ${PROBE_MINIO_HOST} 9000; do sleep 1; done; until nc -z ${PROBE_REDIS_HOST} 6379; do sleep 1; done; python -m app.workers.worker_main" \
  >/dev/null || fail "failed to start worker probe"

for _ in $(seq 1 60); do
  if curl -fsS "http://127.0.0.1:${PROBE_BACKEND_PORT}/api/v1/health" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
curl -fsS "http://127.0.0.1:${PROBE_BACKEND_PORT}/api/v1/health" >/dev/null 2>&1 || fail "backend probe health failed"
pass "backend probe healthy"

echo "[5/7] issue guest token"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"; cleanup' EXIT
API_BASE="http://127.0.0.1:${PROBE_BACKEND_PORT}/api/v1"
curl -sS -X POST "${API_BASE}/auth/guest" > "${TMP_DIR}/guest.json" || fail "guest token request failed"
TOKEN="$(parse_json_field "${TMP_DIR}/guest.json" "access_token")"
[[ -n "${TOKEN}" ]] || fail "guest token empty"
AUTH=(-H "Authorization: Bearer ${TOKEN}")
pass "guest token issued"

echo "[6/7] upload STEP through restored runtime"
curl -sS -X POST "${API_BASE}/files/upload" "${AUTH[@]}" \
  -F "upload=@${STEP_SAMPLE};type=application/step" > "${TMP_DIR}/upload.json" || fail "probe upload request failed"
FILE_ID="$(parse_json_field "${TMP_DIR}/upload.json" "file_id")"
[[ -n "${FILE_ID}" ]] || fail "probe upload file_id empty"
echo "probe_file_id=${FILE_ID}"

STATE=""
for i in $(seq 1 180); do
  curl -sS "${AUTH[@]}" "${API_BASE}/files/${FILE_ID}/status" > "${TMP_DIR}/status.json" || fail "probe status request failed"
  STATE="$(parse_json_field "${TMP_DIR}/status.json" "state")"
  STAGE="$(parse_json_field "${TMP_DIR}/status.json" "stage")"
  PROGRESS="$(parse_json_field "${TMP_DIR}/status.json" "progress_percent")"
  HINT="$(parse_json_field "${TMP_DIR}/status.json" "progress_hint")"
  echo "probe_poll_${i}: state=${STATE} stage=${STAGE:-na} progress=${PROGRESS:-na} hint=${HINT:-na}"
  if [[ "${STATE}" == "succeeded" ]]; then
    break
  fi
  if [[ "${STATE}" == "failed" ]]; then
    fail "probe worker pipeline failed"
  fi
  sleep 2
done
[[ "${STATE}" == "succeeded" ]] || fail "probe worker pipeline did not complete"
pass "worker completed uploaded STEP"

echo "[7/7] verify restored runtime artifacts"
curl -sS "${AUTH[@]}" "${API_BASE}/files/${FILE_ID}" > "${TMP_DIR}/detail.json" || fail "probe detail request failed"
python3 - <<PY || fail "probe file detail contract invalid"
import json
d = json.load(open("${TMP_DIR}/detail.json"))
assert d.get("mode") == "brep", d.get("mode")
assert d.get("status") == "ready", d.get("status")
assert isinstance(d.get("preview_urls"), list) and len(d["preview_urls"]) >= 3
assert isinstance(d.get("gltf_url"), str) and d["gltf_url"]
PY
pass "restored runtime contract verified"

echo "RESULT=PASS"
echo "EVIDENCE=${OUT_FILE}"
