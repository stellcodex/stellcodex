#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EVIDENCE_DIR="${ROOT_DIR}/evidence"
OUT_FILE="${EVIDENCE_DIR}/smoke_gate_output.txt"
API_BASE="${API_BASE:-http://127.0.0.1:8000/api/v1}"
FRONT_BASE="${FRONT_BASE:-http://127.0.0.1:3010}"
STEP_SAMPLE="${STEP_SAMPLE:-/var/stellcodex/work/samples/parca.STEP}"
JPG_SAMPLE="${JPG_SAMPLE:-/var/www/stellcodex/frontend/src/app/gorsel/MASTER1.jpg}"

mkdir -p "${EVIDENCE_DIR}"
exec > >(tee "${OUT_FILE}") 2>&1

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

fail() {
  echo "[FAIL] $1"
  echo "RESULT=FAIL"
  echo "EVIDENCE=${OUT_FILE}"
  exit 1
}

pass() {
  echo "[PASS] $1"
}

parse_json_field() {
  local file="$1"
  local field="$2"
  python3 - <<PY
import json
try:
    data=json.load(open("${file}"))
except Exception:
    data={}
value=data.get("${field}","")
print(value if value is not None else "")
PY
}

echo "# smoke gate"
date -Iseconds
echo "api_base=${API_BASE}"
echo "front_base=${FRONT_BASE}"

echo "[1/8] backend health"
HEALTH_CODE="$(curl -sS -o "${TMP_DIR}/health.json" -w "%{http_code}" "${API_BASE}/health" || true)"
[[ "${HEALTH_CODE}" == "200" ]] || fail "backend health http=${HEALTH_CODE}"
pass "backend health 200"

echo "[2/8] public routes (404 spam guard)"
for path in /upload /dashboard /login /docs /community; do
  code="$(curl -sS -o "${TMP_DIR}/route_$(echo "${path}" | tr '/' '_').html" -w "%{http_code}" "${FRONT_BASE}${path}" || true)"
  [[ "${code}" == "200" ]] || fail "frontend route ${path} http=${code}"
done
pass "public routes return 200"

echo "[3/8] guest token"
curl -sS -X POST "${API_BASE}/auth/guest" > "${TMP_DIR}/guest.json" || fail "guest token request failed"
TOKEN="$(parse_json_field "${TMP_DIR}/guest.json" "access_token")"
[[ -n "${TOKEN}" ]] || fail "guest token empty"
AUTH=(-H "Authorization: Bearer ${TOKEN}")
pass "guest token issued"

create_samples() {
  cat > "${TMP_DIR}/smoke.dxf" <<'DXF'
0
SECTION
2
HEADER
9
$INSUNITS
70
4
0
ENDSEC
0
SECTION
2
TABLES
0
TABLE
2
LAYER
70
1
0
LAYER
2
0
70
0
62
7
6
CONTINUOUS
0
ENDTAB
0
ENDSEC
0
SECTION
2
ENTITIES
0
LINE
8
0
10
0
20
0
11
100
21
0
0
LINE
8
0
10
100
20
0
11
100
21
80
0
LINE
8
0
10
100
20
80
11
0
21
80
0
LINE
8
0
10
0
20
80
11
0
21
0
0
ENDSEC
0
EOF
DXF

}

upload_and_wait_ready() {
  local file_path="$1"
  local content_type="$2"
  local label="$3"
  local upload_json="${TMP_DIR}/upload_${label}.json"
  local status_json="${TMP_DIR}/status_${label}.json"

  curl -sS -X POST "${API_BASE}/files/upload" "${AUTH[@]}" \
    -F "upload=@${file_path};type=${content_type}" > "${upload_json}" || return 1

  local file_id
  file_id="$(parse_json_field "${upload_json}" "file_id")"
  [[ -n "${file_id}" ]] || return 1
  echo "${label}_file_id=${file_id}" >&2

  local state=""
  for i in $(seq 1 180); do
    curl -sS "${AUTH[@]}" "${API_BASE}/files/${file_id}/status" > "${status_json}" || return 1
    state="$(parse_json_field "${status_json}" "state")"
    hint="$(parse_json_field "${status_json}" "progress_hint")"
    stage="$(parse_json_field "${status_json}" "stage")"
    progress="$(parse_json_field "${status_json}" "progress_percent")"
    echo "${label}_poll_${i}: state=${state} stage=${stage:-na} progress=${progress:-na} hint=${hint:-na}" >&2
    if [[ "${state}" == "succeeded" ]]; then
      echo "${file_id}"
      return 0
    fi
    if [[ "${state}" == "failed" ]]; then
      return 1
    fi
    sleep 2
  done
  return 1
}

create_samples
[[ -f "${STEP_SAMPLE}" ]] || fail "step sample missing: ${STEP_SAMPLE}"
[[ -f "${JPG_SAMPLE}" ]] || fail "jpg sample missing: ${JPG_SAMPLE}"

echo "[4/8] jpg upload -> status -> view contract"
JPG_ID="$(upload_and_wait_ready "${JPG_SAMPLE}" "image/jpeg" "jpg")" || fail "jpg upload/status failed"
curl -sS "${AUTH[@]}" "${API_BASE}/files/${JPG_ID}" > "${TMP_DIR}/jpg_detail.json" || fail "jpg detail failed"
JPG_ORIGINAL_URL="$(parse_json_field "${TMP_DIR}/jpg_detail.json" "original_url")"
[[ -n "${JPG_ORIGINAL_URL}" ]] || fail "jpg original_url empty"
JPG_ORIGINAL_HTTP="$(curl -sS -o /dev/null -w "%{http_code}" "${AUTH[@]}" "http://127.0.0.1:8000${JPG_ORIGINAL_URL}" || true)"
[[ "${JPG_ORIGINAL_HTTP}" == "200" ]] || fail "jpg original asset http=${JPG_ORIGINAL_HTTP}"
JPG_VIEW_HTTP="$(curl -sS -o "${TMP_DIR}/jpg_view.html" -w "%{http_code}" "${FRONT_BASE}/view/${JPG_ID}" || true)"
[[ "${JPG_VIEW_HTTP}" == "200" ]] || fail "jpg view route http=${JPG_VIEW_HTTP}"
pass "jpg flow ok"

echo "[5/8] dxf upload -> status -> manifest/render"
DXF_ID="$(upload_and_wait_ready "${TMP_DIR}/smoke.dxf" "application/dxf" "dxf")" || fail "dxf upload/status failed"
DXF_MANIFEST_HTTP="$(curl -sS -o "${TMP_DIR}/dxf_manifest.json" -w "%{http_code}" "${AUTH[@]}" "${API_BASE}/files/${DXF_ID}/dxf/manifest" || true)"
[[ "${DXF_MANIFEST_HTTP}" == "200" ]] || fail "dxf manifest http=${DXF_MANIFEST_HTTP}"
DXF_RENDER_HTTP="$(curl -sS -o "${TMP_DIR}/dxf_render.svg" -w "%{http_code}" "${AUTH[@]}" "${API_BASE}/files/${DXF_ID}/dxf/render?layers=0" || true)"
[[ "${DXF_RENDER_HTTP}" == "200" ]] || fail "dxf render http=${DXF_RENDER_HTTP}"
grep -q "<svg" "${TMP_DIR}/dxf_render.svg" || fail "dxf render missing svg tag"
grep -q "translate(0," "${TMP_DIR}/dxf_render.svg" || fail "dxf render missing fit translate transform"
DXF_VIEW_HTTP="$(curl -sS -o "${TMP_DIR}/dxf_view.html" -w "%{http_code}" "${FRONT_BASE}/view/${DXF_ID}" || true)"
[[ "${DXF_VIEW_HTTP}" == "200" ]] || fail "dxf view route http=${DXF_VIEW_HTTP}"
pass "dxf flow ok"

echo "[6/8] step upload -> status -> parts metadata"
STEP_ID="$(upload_and_wait_ready "${STEP_SAMPLE}" "application/step" "step")" || fail "step upload/status failed"
curl -sS "${AUTH[@]}" "${API_BASE}/files/${STEP_ID}/manifest" > "${TMP_DIR}/step_manifest.json" || fail "step manifest failed"
PART_COUNT="$(parse_json_field "${TMP_DIR}/step_manifest.json" "part_count")"
[[ -n "${PART_COUNT}" && "${PART_COUNT}" != "None" ]] || fail "step manifest part_count empty"
python3 - <<PY || fail "step part_count is not > 0"
value = int("${PART_COUNT}")
assert value > 0
PY
STEP_VIEW_HTTP="$(curl -sS -o "${TMP_DIR}/step_view.html" -w "%{http_code}" "${FRONT_BASE}/view/${STEP_ID}" || true)"
[[ "${STEP_VIEW_HTTP}" == "200" ]] || fail "step view route http=${STEP_VIEW_HTTP}"
pass "step flow ok"

echo "[7/8] share create -> resolve -> frontend share route"
curl -sS -X POST "${AUTH[@]}" -H "Content-Type: application/json" -d '{}' \
  "${API_BASE}/files/${STEP_ID}/share" > "${TMP_DIR}/share_create.json" || fail "share create failed"
SHARE_TOKEN="$(parse_json_field "${TMP_DIR}/share_create.json" "token")"
[[ -n "${SHARE_TOKEN}" ]] || fail "share token empty"

SHARE_RESOLVE_HTTP="$(curl -sS -o "${TMP_DIR}/share_resolve.json" -w "%{http_code}" "${API_BASE}/shares/${SHARE_TOKEN}" || true)"
[[ "${SHARE_RESOLVE_HTTP}" == "200" ]] || fail "share resolve http=${SHARE_RESOLVE_HTTP}"
RESOLVED_FILE_ID="$(parse_json_field "${TMP_DIR}/share_resolve.json" "file_id")"
[[ "${RESOLVED_FILE_ID}" == "${STEP_ID}" ]] || fail "share resolved file mismatch"
SHARE_FRONT_HTTP="$(curl -sS -o "${TMP_DIR}/share_front.html" -w "%{http_code}" "${FRONT_BASE}/share/${SHARE_TOKEN}" || true)"
[[ "${SHARE_FRONT_HTTP}" == "200" ]] || fail "frontend share route http=${SHARE_FRONT_HTTP}"
pass "share flow ok"

echo "[8/8] smoke summary"
echo "jpg_id=${JPG_ID}"
echo "dxf_id=${DXF_ID}"
echo "step_id=${STEP_ID}"
echo "share_token=${SHARE_TOKEN}"
echo "RESULT=PASS"
echo "EVIDENCE=${OUT_FILE}"
