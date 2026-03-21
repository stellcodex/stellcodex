#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${ROOT_DIR}/scripts/lib/runtime_env.sh"

EVIDENCE_DIR="${ROOT_DIR}/evidence"
OUT_FILE="${EVIDENCE_DIR}/object_restore_drill_output.txt"
LISTING_FILE="${EVIDENCE_DIR}/object_restore_probe_listing.txt"
MIRROR_ROOT="${MIRROR_ROOT:-${ROOT_DIR}/backups/object_mirror}"
BUCKET="${BUCKET:-stellcodex}"
PROBE_PORT="${PROBE_PORT:-19000}"
PROBE_NAME="${PROBE_NAME:-minio_restore_probe}"
PROBE_IMAGE="${PROBE_IMAGE:-}"
PROBE_ACCESS_KEY="${PROBE_ACCESS_KEY:-restoreprobe}"
PROBE_SECRET_KEY="${PROBE_SECRET_KEY:-restoreprobe123}"
LIVE_MINIO_CONTAINER="${LIVE_MINIO_CONTAINER:-$(runtime_resolve_minio_container 2>/dev/null || true)}"
AWS_REGION="${AWS_REGION:-us-east-1}"

mkdir -p "${EVIDENCE_DIR}"
exec > >(tee "${OUT_FILE}") 2>&1

fail() {
  echo "[FAIL] $1"
  echo "RESULT=FAIL"
  echo "EVIDENCE=${OUT_FILE}"
  exit 1
}

pass() {
  echo "[PASS] $1"
}

pick_probe_port() {
  local candidate
  for candidate in "${PROBE_PORT}" 19010 19020 19100 19110 19200 19300 19400; do
    if ! ss -ltn "( sport = :${candidate} )" 2>/dev/null | tail -n +2 | grep -q .; then
      echo "${candidate}"
      return 0
    fi
  done
  return 1
}

cleanup() {
  if docker inspect "${PROBE_NAME}" >/dev/null 2>&1; then
    docker rm -f "${PROBE_NAME}" >/dev/null 2>&1 || true
  fi
  if [[ -n "${PROBE_DATA_ROOT:-}" ]] && [[ -d "${PROBE_DATA_ROOT}" ]]; then
    rm -rf "${PROBE_DATA_ROOT}"
  fi
}

trap cleanup EXIT

echo "# Object restore drill"
date -Iseconds
echo "mirror_root=${MIRROR_ROOT}"
echo "bucket=${BUCKET}"

command -v docker >/dev/null 2>&1 || fail "docker is required"
command -v ss >/dev/null 2>&1 || fail "ss is required"

[[ -d "${MIRROR_ROOT}/${BUCKET}" ]] || fail "mirror bucket path missing: ${MIRROR_ROOT}/${BUCKET}"

if [[ -z "${PROBE_IMAGE}" ]]; then
  PROBE_IMAGE="$(docker inspect "${LIVE_MINIO_CONTAINER}" --format '{{.Config.Image}}' 2>/dev/null || true)"
fi
[[ -n "${PROBE_IMAGE}" ]] || fail "unable to determine MinIO probe image"

PROBE_PORT="$(pick_probe_port)" || fail "no free probe port available for restore probe"
echo "probe_port=${PROBE_PORT}"

PROBE_DATA_ROOT="$(mktemp -d /tmp/object-restore-probe-XXXXXX)"
cp -r "${MIRROR_ROOT}/${BUCKET}" "${PROBE_DATA_ROOT}/"
pass "probe data copied to ${PROBE_DATA_ROOT}"

LOCAL_FILE_COUNT="$(find "${MIRROR_ROOT}/${BUCKET}" -type f | wc -l | tr -d ' ')"
[[ "${LOCAL_FILE_COUNT}" -gt 0 ]] || fail "mirror bucket contains no files"
echo "local_file_count=${LOCAL_FILE_COUNT}"

docker run -d --rm \
  --name "${PROBE_NAME}" \
  -p "${PROBE_PORT}:9000" \
  -e MINIO_ROOT_USER="${PROBE_ACCESS_KEY}" \
  -e MINIO_ROOT_PASSWORD="${PROBE_SECRET_KEY}" \
  -v "${PROBE_DATA_ROOT}:/data" \
  "${PROBE_IMAGE}" server /data >/dev/null || fail "failed to start MinIO restore probe"

for _ in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${PROBE_PORT}/minio/health/live" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
curl -fsS "http://127.0.0.1:${PROBE_PORT}/minio/health/live" >/dev/null 2>&1 || fail "restore probe health check failed"
pass "restore probe live on port ${PROBE_PORT}"

PROBE_FILE_COUNT="$(find "${PROBE_DATA_ROOT}/${BUCKET}" -type f | wc -l | tr -d ' ')"
[[ "${PROBE_FILE_COUNT}" -gt 0 ]] || fail "probe data root contains no files"
echo "probe_file_count=${PROBE_FILE_COUNT}"
[[ "${LOCAL_FILE_COUNT}" == "${PROBE_FILE_COUNT}" ]] || fail "file count mismatch local=${LOCAL_FILE_COUNT} probe=${PROBE_FILE_COUNT}"

docker exec "${PROBE_NAME}" sh -lc "ls /data/${BUCKET}" | sort > "${LISTING_FILE}"
grep -q '^packages$' "${LISTING_FILE}" || fail "restored bucket missing packages/ prefix"
grep -q '^uploads$' "${LISTING_FILE}" || fail "restored bucket missing uploads/ prefix"

PACKAGE_SAMPLE="$(docker exec "${PROBE_NAME}" sh -lc "for f in /data/${BUCKET}/packages/*/production_package.zip; do printf '%s\n' \"\$f\"; break; done" 2>/dev/null | sed "s#^/data/${BUCKET}/##")"
UPLOAD_SAMPLE="$(docker exec "${PROBE_NAME}" sh -lc "for f in /data/${BUCKET}/uploads/*/*/*/original/xl.meta; do if [ -e \"\$f\" ]; then printf '%s\n' \"\$f\"; break; fi; done" 2>/dev/null | sed "s#^/data/${BUCKET}/##")"
[[ -n "${PACKAGE_SAMPLE}" ]] || fail "restored bucket returned no package sample"
[[ -n "${UPLOAD_SAMPLE}" ]] || fail "restored bucket returned no upload sample"
echo "package_sample=${PACKAGE_SAMPLE}"
echo "upload_sample=${UPLOAD_SAMPLE}"

pass "object restore drill verified"
echo "RESULT=PASS"
echo "EVIDENCE=${OUT_FILE}"
