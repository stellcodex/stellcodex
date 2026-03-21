#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${ROOT_DIR}/scripts/lib/runtime_env.sh"

BACKEND_BASE_URL="${BACKEND_BASE_URL:-$(runtime_resolve_backend_base_url)}"
API_BASE="${API_BASE:-${BACKEND_BASE_URL%/}/api/v1}"
FRONT_BASE="${FRONT_BASE:-$(runtime_resolve_front_base_url)}"
REPORT_DIR="${REPORT_DIR:-${ROOT_DIR}/evidence}"
TMP_DIR="$(mktemp -d)"
OUT_FILE="${REPORT_DIR}/e2e_smoke_output.txt"

mkdir -p "${REPORT_DIR}"
trap 'rm -rf "${TMP_DIR}"' EXIT
exec > >(tee "${OUT_FILE}") 2>&1

pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; exit 1; }

json_field() {
  local file="$1"
  local field="$2"
  python3 - "$file" "$field" <<'PY'
import json,sys
path,field=sys.argv[1],sys.argv[2]
try:
    data=json.load(open(path))
except Exception:
    data={}
value=data.get(field,"")
print(value if value is not None else "")
PY
}

echo "E2E_SMOKE_START=$(date -Iseconds)"
echo "api_base=${API_BASE}"
echo "front_base=${FRONT_BASE}"

echo "stage=health"
HEALTH_HTTP="$(curl -sS -o "${TMP_DIR}/health.json" -w "%{http_code}" "${API_BASE}/health" || true)"
[[ "${HEALTH_HTTP}" == "200" ]] || fail "health endpoint http=${HEALTH_HTTP}"
pass "health endpoint 200"

echo "stage=auth_session"
TOKEN="$(runtime_request_auth_token "${API_BASE}" 2>/dev/null || true)"
[[ -n "${TOKEN}" ]] || fail "auth token missing"
AUTH=(-H "Authorization: Bearer ${TOKEN}")
pass "auth session created"

echo "stage=create_test_file"
cat > "${TMP_DIR}/test.md" <<'MD'
# STELLCODEX E2E

This is an automated smoke payload.
- upload
- process
- analyze
- share
MD
[[ -f "${TMP_DIR}/test.md" ]] || fail "test.md was not created"
pass "test.md created"

echo "stage=upload"
curl -sS -X POST "${API_BASE}/files/upload" "${AUTH[@]}" \
  -F "upload=@${TMP_DIR}/test.md;type=text/markdown" > "${TMP_DIR}/upload.json" || fail "upload request failed"
FILE_ID="$(json_field "${TMP_DIR}/upload.json" "file_id")"
[[ -n "${FILE_ID}" ]] || fail "upload did not return file_id"
echo "file_id=${FILE_ID}"
pass "upload accepted"

echo "stage=poll_status"
STATE=""
for i in $(seq 1 120); do
  curl -sS "${AUTH[@]}" "${API_BASE}/files/${FILE_ID}/status" > "${TMP_DIR}/status.json" || fail "status request failed"
  STATE="$(json_field "${TMP_DIR}/status.json" "state")"
  STAGE="$(json_field "${TMP_DIR}/status.json" "stage")"
  echo "poll_${i}: state=${STATE} stage=${STAGE}"
  if [[ "${STATE}" == "succeeded" ]]; then
    break
  fi
  if [[ "${STATE}" == "failed" ]]; then
    fail "job failed"
  fi
  sleep 2
done
[[ "${STATE}" == "succeeded" ]] || fail "job did not reach succeeded"
pass "status succeeded"

echo "stage=file_detail"
DETAIL_HTTP="$(curl -sS -o "${TMP_DIR}/detail.json" -w "%{http_code}" "${AUTH[@]}" "${API_BASE}/files/${FILE_ID}" || true)"
[[ "${DETAIL_HTTP}" == "200" ]] || fail "file detail http=${DETAIL_HTTP}"
DETAIL_STATUS="$(json_field "${TMP_DIR}/detail.json" "status")"
[[ -n "${DETAIL_STATUS}" ]] || fail "file detail missing status"
pass "file detail loaded"

echo "stage=agent_run"
cat > "${TMP_DIR}/agent.json" <<JSON
{"agent_id":"data_analysis_agent","file_id":"${FILE_ID}","prompt":"quick smoke summary","include_web_context":false}
JSON
AGENT_HTTP="$(curl -sS -o "${TMP_DIR}/agent_out.json" -w "%{http_code}" "${AUTH[@]}" -H "Content-Type: application/json" -X POST "${API_BASE}/stell-ai/agents/run" --data @"${TMP_DIR}/agent.json" || true)"
[[ "${AGENT_HTTP}" == "200" ]] || fail "agent run http=${AGENT_HTTP}"
AGENT_STATUS="$(json_field "${TMP_DIR}/agent_out.json" "status")"
[[ "${AGENT_STATUS}" == "ok" ]] || fail "agent run status=${AGENT_STATUS}"
pass "agent run ok"

echo "stage=share_create"
curl -sS -X POST "${API_BASE}/files/${FILE_ID}/share" "${AUTH[@]}" \
  -H "Content-Type: application/json" \
  -d '{"permission":"download","expires_in_seconds":86400}' > "${TMP_DIR}/share_create.json" || fail "share create failed"
SHARE_TOKEN="$(json_field "${TMP_DIR}/share_create.json" "token")"
[[ -n "${SHARE_TOKEN}" ]] || fail "share token missing"
echo "share_token=${SHARE_TOKEN}"
pass "share token created"

echo "stage=share_resolve"
SHARE_HTTP="$(curl -sS -o "${TMP_DIR}/share_resolve.json" -w "%{http_code}" "${API_BASE}/shares/${SHARE_TOKEN}" || true)"
[[ "${SHARE_HTTP}" == "200" ]] || fail "share resolve http=${SHARE_HTTP}"
CAN_DOWNLOAD="$(json_field "${TMP_DIR}/share_resolve.json" "can_download")"
[[ "${CAN_DOWNLOAD}" == "True" || "${CAN_DOWNLOAD}" == "true" ]] || fail "share can_download=${CAN_DOWNLOAD}"
pass "share resolve ok"

echo "stage=share_download"
CONTENT_HTTP="$(curl -sS -o "${TMP_DIR}/share_content.bin" -w "%{http_code}" "${API_BASE}/share/${SHARE_TOKEN}/content" || true)"
[[ "${CONTENT_HTTP}" == "200" ]] || fail "share content http=${CONTENT_HTTP}"
CONTENT_SIZE="$(wc -c < "${TMP_DIR}/share_content.bin" | tr -d ' ')"
[[ "${CONTENT_SIZE}" -gt 0 ]] || fail "share content empty"
pass "share content downloaded (${CONTENT_SIZE} bytes)"

echo "stage=share_front_route"
FRONT_HTTP="$(curl -sS -o /dev/null -w "%{http_code}" "${FRONT_BASE}/share/${SHARE_TOKEN}" || true)"
[[ "${FRONT_HTTP}" != "404" ]] || fail "front share route returned 404"
pass "front share route non-404 (${FRONT_HTTP})"

echo "RESULT=PASS"
echo "EVIDENCE=${OUT_FILE}"
