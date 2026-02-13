#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EVIDENCE_DIR="${ROOT_DIR}/evidence"
COMPOSE_DIR="${ROOT_DIR}/infrastructure/deploy"
TS="$(date +%Y%m%d_%H%M%S)"
EVIDENCE_FILE="${EVIDENCE_DIR}/smoke_gate_${TS}.txt"

mkdir -p "${EVIDENCE_DIR}"
exec > >(tee "${EVIDENCE_FILE}") 2>&1

fail() {
  echo "SMOKE_GATE FAIL: $1"
  echo "RESULT=FAIL"
  echo "EVIDENCE=${EVIDENCE_FILE}"
  exit 1
}

echo "# smoke gate"
date -Iseconds

echo "[1/9] frontend build"
(
  cd "${ROOT_DIR}/frontend"
  npm run build
) || fail "frontend build failed"

echo "[2/9] backend unittest"
(
  cd "${ROOT_DIR}"
  python3 -m unittest -q backend/tests/test_hybrid_v1_geometry_merge_policy.py
) || fail "backend unittest failed"

echo "[3/9] admin token + admin health"
ADMIN_TOKEN="$(
  cd "${COMPOSE_DIR}" && docker-compose exec -T backend python - <<'PY'
from app.db.session import SessionLocal
from app.models.user import User
from app.security.jwt import create_user_token

db = SessionLocal()
try:
    admin = db.query(User).filter(User.role == "admin").first()
    if admin is None:
        admin = User(
            email="smoke.admin@stellcodex.local",
            role="admin",
            is_suspended=False,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
    print(create_user_token(str(admin.id), admin.role))
finally:
    db.close()
PY
)" || fail "failed to generate admin token"
[[ -n "${ADMIN_TOKEN}" ]] || fail "admin token empty"
echo "admin_token_len=${#ADMIN_TOKEN}"

ADMIN_HEALTH_CODE="$(
  curl -sS -o "/tmp/smoke_admin_health_${TS}.json" -w "%{http_code}" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}" \
    "http://127.0.0.1:8000/api/v1/admin/health" || true
)"
echo "admin_health_http=${ADMIN_HEALTH_CODE}"
[[ "${ADMIN_HEALTH_CODE}" == "200" ]] || fail "admin health http=${ADMIN_HEALTH_CODE}"

echo "[4/9] backend health"
API_CODE="$(curl -sS -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/v1/health || true)"
echo "backend_health_http=${API_CODE}"
[[ "${API_CODE}" == "200" ]] || fail "backend health http=${API_CODE}"

echo "[5/9] admin failures route contract"
ADMIN_FAILURES_NOAUTH_CODE="$(
  curl -sS -o "/tmp/smoke_admin_failures_noauth_${TS}.json" -w "%{http_code}" \
    "http://127.0.0.1:8000/api/v1/admin/failures?limit=20" || true
)"
echo "admin_failures_noauth_http=${ADMIN_FAILURES_NOAUTH_CODE}"
[[ "${ADMIN_FAILURES_NOAUTH_CODE}" != "404" ]] || fail "admin failures route returned 404"

ADMIN_FAILURES_AUTH_CODE="$(
  curl -sS -o "/tmp/smoke_admin_failures_auth_${TS}.json" -w "%{http_code}" \
    -H "Authorization: Bearer ${ADMIN_TOKEN}" \
    "http://127.0.0.1:8000/api/v1/admin/failures?limit=20" || true
)"
echo "admin_failures_auth_http=${ADMIN_FAILURES_AUTH_CODE}"
[[ "${ADMIN_FAILURES_AUTH_CODE}" == "200" ]] || fail "admin failures auth http=${ADMIN_FAILURES_AUTH_CODE}"

echo "[6/9] frontend root + static asset"
HOME_CODE="$(curl -sS -o /tmp/smoke_home_${TS}.html -w "%{http_code}" http://127.0.0.1:3000/ || true)"
echo "frontend_root_http=${HOME_CODE}"
[[ "${HOME_CODE}" == "200" ]] || fail "frontend root http=${HOME_CODE}"

ASSET_PATH="/favicon.ico"
ASSET_CODE="$(curl -sS -o /dev/null -w "%{http_code}" "http://127.0.0.1:3000${ASSET_PATH}" || true)"
echo "frontend_asset_path=${ASSET_PATH}"
echo "frontend_asset_http=${ASSET_CODE}"
[[ "${ASSET_CODE}" == "200" ]] || fail "frontend static asset http=${ASSET_CODE}"

echo "[7/9] upload + status contract"
SAMPLE="/var/stellcodex/work/samples/parca.STEP"
if [[ ! -f "${SAMPLE}" ]]; then
  SAMPLE="$(ls -1 /var/stellcodex/work/samples/* 2>/dev/null | head -n1 || true)"
fi
[[ -n "${SAMPLE}" ]] || fail "sample file not found under /var/stellcodex/work/samples"
echo "sample=${SAMPLE}"

GUEST_JSON="${EVIDENCE_DIR}/smoke_gate_guest_${TS}.json"
UPLOAD_JSON="${EVIDENCE_DIR}/smoke_gate_upload_${TS}.json"
JOB_JSON="${EVIDENCE_DIR}/smoke_gate_job_${TS}.json"

curl -sS -X POST http://127.0.0.1:8000/api/v1/auth/guest > "${GUEST_JSON}" || fail "auth/guest request failed"
TOKEN="$(python3 - <<PY
import json
print(json.load(open('${GUEST_JSON}'))['access_token'])
PY
)"
echo "guest_token_len=${#TOKEN}"

curl -sS -X POST http://127.0.0.1:8000/api/v1/upload \
  -H "Authorization: Bearer ${TOKEN}" \
  -F "file=@${SAMPLE}" > "${UPLOAD_JSON}" || fail "upload request failed"
cat "${UPLOAD_JSON}"

PROJECT_ID="$(python3 - <<PY
import json
j=json.load(open('${UPLOAD_JSON}'))
print(j.get('project_id',''))
PY
)"
REVISION_ID="$(python3 - <<PY
import json
j=json.load(open('${UPLOAD_JSON}'))
print(j.get('revision_id',''))
PY
)"
FILE_ID="$(python3 - <<PY
import json
j=json.load(open('${UPLOAD_JSON}'))
print(j.get('file_id',''))
PY
)"
JOB_ID="$(python3 - <<PY
import json
j=json.load(open('${UPLOAD_JSON}'))
print(j.get('job_id',''))
PY
)"
echo "project_id=${PROJECT_ID}"
echo "revision_id=${REVISION_ID}"
echo "file_id=${FILE_ID}"
echo "job_id=${JOB_ID}"
[[ -n "${FILE_ID}" ]] || fail "upload response missing file_id"

STATUS_REV_CODE="$(curl -sS -o /tmp/smoke_status_rev_${TS}.json -w "%{http_code}" "http://127.0.0.1:8000/api/v1/status/${REVISION_ID}" || true)"
STATUS_FILE_CODE="$(curl -sS -o /tmp/smoke_status_file_${TS}.json -w "%{http_code}" "http://127.0.0.1:8000/api/v1/status/${FILE_ID}" || true)"
echo "status_revision_http=${STATUS_REV_CODE}"
echo "status_file_http=${STATUS_FILE_CODE}"
[[ "${STATUS_REV_CODE}" == "200" ]] || fail "status by revision_id http=${STATUS_REV_CODE}"
[[ "${STATUS_FILE_CODE}" == "200" ]] || fail "status by file_id http=${STATUS_FILE_CODE}"

echo "[8/9] job wait until finished"
FINAL_STATUS=""
for i in $(seq 1 90); do
  curl -sS "http://127.0.0.1:8000/api/v1/jobs/${JOB_ID}" > "${JOB_JSON}" || fail "jobs status request failed"
  STATUS="$(python3 - <<PY
import json
print(json.load(open('${JOB_JSON}')).get('status',''))
PY
)"
  echo "job_poll_${i}=${STATUS}"
  if [[ "${STATUS}" == "finished" || "${STATUS}" == "failed" ]]; then
    FINAL_STATUS="${STATUS}"
    break
  fi
  sleep 2
done
[[ -n "${FINAL_STATUS}" ]] || fail "job did not reach terminal state"
[[ "${FINAL_STATUS}" == "finished" ]] || fail "job terminal status=${FINAL_STATUS}"

echo "[9/9] model endpoint + MinIO artefacts"
FILE_STATUS_CODE="$(curl -sS -o /tmp/smoke_file_status_${TS}.json -w "%{http_code}" -H "Authorization: Bearer ${TOKEN}" "http://127.0.0.1:8000/api/v1/files/${FILE_ID}/status" || true)"
LOD0_CODE="$(curl -sS -o /dev/null -w "%{http_code}" -H "Authorization: Bearer ${TOKEN}" "http://127.0.0.1:8000/api/v1/files/${FILE_ID}/lod/lod0" || true)"
echo "files_status_http=${FILE_STATUS_CODE}"
echo "files_lod0_http=${LOD0_CODE}"
[[ "${FILE_STATUS_CODE}" == "200" ]] || fail "files status http=${FILE_STATUS_CODE}"
[[ "${LOD0_CODE}" == "200" ]] || fail "files lod0 http=${LOD0_CODE}"

PREFIX="models/${PROJECT_ID}/${REVISION_ID}/"
MINIO_LOG="${EVIDENCE_DIR}/smoke_gate_minio_${TS}.txt"
MINIO_REPORT="$(
  cd "${COMPOSE_DIR}" && docker-compose exec -T backend python - <<PY
import os, boto3
bucket=os.environ['STELLCODEX_S3_BUCKET']
endpoint=os.environ['STELLCODEX_S3_ENDPOINT_URL']
key=os.environ['STELLCODEX_S3_ACCESS_KEY_ID']
secret=os.environ['STELLCODEX_S3_SECRET_ACCESS_KEY']
prefix='${PREFIX}'
s3=boto3.client('s3', endpoint_url=endpoint, aws_access_key_id=key, aws_secret_access_key=secret)
items=s3.list_objects_v2(Bucket=bucket, Prefix=prefix).get('Contents', [])
keys=[item['Key'] for item in items]
print(f"bucket={bucket}")
print(f"prefix={prefix}")
print(f"count={len(keys)}")
for k in keys:
    print(k)
required=['lod0.glb','meta.json','thumb.webp']
for suffix in required:
    print(f"has_{suffix}={any(k.endswith(suffix) for k in keys)}")
missing=[suffix for suffix in required if not any(k.endswith(suffix) for k in keys)]
if missing:
    raise SystemExit("missing artefacts: " + ",".join(missing))
PY
)" || fail "minio artefact validation failed"
printf "%s\n" "${MINIO_REPORT}" | tee "${MINIO_LOG}"
echo "minio_log=${MINIO_LOG}"

echo "SMOKE_GATE PASS"
echo "RESULT=PASS"
echo "EVIDENCE=${EVIDENCE_FILE}"
