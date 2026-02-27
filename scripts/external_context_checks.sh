#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EVIDENCE_DIR="${ROOT_DIR}/evidence/external_context_fix"
EVIDENCE_FILE="${EVIDENCE_DIR}/02_external_context_checks_run.txt"

mkdir -p "${EVIDENCE_DIR}"
exec > >(tee "${EVIDENCE_FILE}") 2>&1

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

PASS_COUNT=0
FAIL_COUNT=0
FAIL_ITEMS=()
CHECK_DETAIL=""

record_result() {
  local label="$1"
  local status="$2"
  local detail="$3"
  if [[ "${status}" == "PASS" ]]; then
    PASS_COUNT=$((PASS_COUNT + 1))
  else
    FAIL_COUNT=$((FAIL_COUNT + 1))
    FAIL_ITEMS+=("${label}: ${detail}")
  fi
  echo "${label} ${status}: ${detail}"
}

run_check() {
  local label="$1"
  shift
  CHECK_DETAIL=""
  if "$@"; then
    record_result "${label}" "PASS" "${CHECK_DETAIL:-ok}"
  else
    record_result "${label}" "FAIL" "${CHECK_DETAIL:-failed}"
  fi
}

extract_json_field() {
  local json_file="$1"
  local field_name="$2"
  python3 - "$json_file" "$field_name" <<'PY'
import json
import sys

json_file = sys.argv[1]
field_name = sys.argv[2]
try:
    with open(json_file, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
except Exception:
    print("")
    raise SystemExit(0)
value = payload.get(field_name, "")
if isinstance(value, str):
    print(value)
else:
    print("")
PY
}

extract_status_value() {
  local json_file="$1"
  python3 - "$json_file" <<'PY'
import json
import sys

try:
    with open(sys.argv[1], "r", encoding="utf-8") as fh:
        payload = json.load(fh)
except Exception:
    print("")
    raise SystemExit(0)
for key in ("state", "status", "progress_hint"):
    value = payload.get(key)
    if isinstance(value, str) and value:
        print(value)
        raise SystemExit(0)
print("")
PY
}

find_sample_file() {
  local sample="/var/stellcodex/work/samples/parca.STEP"
  if [[ -f "${sample}" ]]; then
    echo "${sample}"
    return 0
  fi
  sample="$(ls -1 /var/stellcodex/work/samples/* 2>/dev/null | head -n1 || true)"
  if [[ -n "${sample}" && -f "${sample}" ]]; then
    echo "${sample}"
    return 0
  fi
  return 1
}

check_a_headers() {
  local headers_file="${TMP_DIR}/a_headers.txt"
  curl -sSI https://stellcodex.com | sed 's/\r$//' > "${headers_file}"
  local status_line
  status_line="$(head -n1 "${headers_file}" || true)"
  local cf_header
  cf_header="$(grep -Eim1 '^(cf-ray|cf-cache-status|server: cloudflare):' "${headers_file}" || true)"
  echo "A.status=${status_line}"
  echo "A.cf_header=${cf_header:-<missing>}"
  if [[ "${status_line}" =~ ^HTTP/[0-9.]+\ 200\  ]] && [[ -n "${cf_header}" ]]; then
    CHECK_DETAIL="status=200 and cf_header_present"
    return 0
  fi
  CHECK_DETAIL="status_or_cf_header_missing"
  return 1
}

check_b_public_health() {
  local body_file="${TMP_DIR}/b_public_health.json"
  local code
  code="$(curl -sS -o "${body_file}" -w "%{http_code}" https://stellcodex.com/api/v1/health || true)"
  local body
  body="$(tr -d '\n' < "${body_file}" | cut -c1-240)"
  echo "B.http=${code}"
  echo "B.body=${body}"
  if [[ "${code}" == "200" ]]; then
    CHECK_DETAIL="http=200"
    return 0
  fi
  CHECK_DETAIL="http=${code}"
  return 1
}

check_c_local_health() {
  local body_file="${TMP_DIR}/c_local_health.json"
  local code
  code="$(curl -sS -o "${body_file}" -w "%{http_code}" http://127.0.0.1:8000/api/v1/health || true)"
  local body
  body="$(tr -d '\n' < "${body_file}" | cut -c1-240)"
  echo "C.http=${code}"
  echo "C.body=${body}"
  if [[ "${code}" == "200" ]]; then
    CHECK_DETAIL="http=200"
    return 0
  fi
  CHECK_DETAIL="http=${code}"
  return 1
}

check_d_dns_hosts() {
  local hosts_out
  hosts_out="$(getent hosts stellcodex.com || true)"
  echo "D.getent_hosts_output:"
  if [[ -n "${hosts_out}" ]]; then
    echo "${hosts_out}"
    CHECK_DETAIL="host_records_present"
    return 0
  fi
  echo "<empty>"
  CHECK_DETAIL="no_host_records"
  return 1
}

canonical_upload_flow() {
  local sample_file="$1"
  local guest_json="${TMP_DIR}/e_guest.json"
  local upload_json="${TMP_DIR}/e_upload.json"
  local status_json="${TMP_DIR}/e_status.json"

  local guest_code
  guest_code="$(curl -sS -o "${guest_json}" -w "%{http_code}" -X POST https://stellcodex.com/api/v1/auth/guest || true)"
  if [[ "${guest_code}" != "200" ]]; then
    CHECK_DETAIL="auth_guest_http=${guest_code}"
    return 1
  fi

  local token
  token="$(extract_json_field "${guest_json}" "access_token")"
  echo "E.guest_token_len=${#token}"
  if [[ -z "${token}" ]]; then
    CHECK_DETAIL="guest_token_missing"
    return 1
  fi

  local upload_code
  upload_code="$(curl -sS -o "${upload_json}" -w "%{http_code}" -X POST \
    -H "Authorization: Bearer ${token}" \
    -F "upload=@${sample_file}" \
    https://stellcodex.com/api/v1/files/upload || true)"
  if [[ "${upload_code}" != "200" ]]; then
    CHECK_DETAIL="upload_http=${upload_code}"
    return 1
  fi

  local file_id
  file_id="$(extract_json_field "${upload_json}" "file_id")"
  local status_value
  status_value="$(extract_json_field "${upload_json}" "status")"
  local job_id
  job_id="$(extract_json_field "${upload_json}" "job_id")"
  echo "E.file_id=${file_id}"
  echo "E.upload_status=${status_value:-<none>}"
  echo "E.job_id_present=$([[ -n "${job_id}" ]] && echo yes || echo no)"

  if [[ ! "${file_id}" =~ ^scx_ ]]; then
    CHECK_DETAIL="invalid_file_id"
    return 1
  fi

  local status_code
  status_code="$(curl -sS -o "${status_json}" -w "%{http_code}" \
    -H "Authorization: Bearer ${token}" \
    "https://stellcodex.com/api/v1/files/${file_id}/status" || true)"
  local state
  state="$(extract_status_value "${status_json}")"
  echo "E.status_http=${status_code}"
  echo "E.status_value=${state:-<none>}"

  if [[ "${status_code}" != "200" ]]; then
    CHECK_DETAIL="status_http=${status_code}"
    return 1
  fi

  CHECK_DETAIL="file_id=${file_id} status_http=200"
  return 0
}

legacy_upload_flow() {
  local sample_file="$1"
  local guest_json="${TMP_DIR}/f_guest.json"
  local upload_json="${TMP_DIR}/f_upload.json"
  local status_json="${TMP_DIR}/f_status.json"

  local guest_code
  guest_code="$(curl -sS -o "${guest_json}" -w "%{http_code}" -X POST https://stellcodex.com/api/v1/auth/guest || true)"
  if [[ "${guest_code}" != "200" ]]; then
    CHECK_DETAIL="auth_guest_http=${guest_code}"
    return 1
  fi

  local token
  token="$(extract_json_field "${guest_json}" "access_token")"
  echo "F.guest_token_len=${#token}"
  if [[ -z "${token}" ]]; then
    CHECK_DETAIL="guest_token_missing"
    return 1
  fi

  local upload_code
  local field_used="file"
  upload_code="$(curl -sS -o "${upload_json}" -w "%{http_code}" -X POST \
    -H "Authorization: Bearer ${token}" \
    -F "file=@${sample_file}" \
    https://stellcodex.com/api/v1/upload || true)"

  local file_id
  file_id="$(extract_json_field "${upload_json}" "file_id")"
  if [[ "${upload_code}" != "200" || -z "${file_id}" ]]; then
    field_used="upload"
    upload_code="$(curl -sS -o "${upload_json}" -w "%{http_code}" -X POST \
      -H "Authorization: Bearer ${token}" \
      -F "upload=@${sample_file}" \
      https://stellcodex.com/api/v1/upload || true)"
    file_id="$(extract_json_field "${upload_json}" "file_id")"
  fi

  echo "F.field_used=${field_used}"
  echo "F.upload_http=${upload_code}"
  echo "F.file_id=${file_id}"

  if [[ "${upload_code}" != "200" ]]; then
    CHECK_DETAIL="legacy_upload_http=${upload_code}"
    return 1
  fi
  if [[ ! "${file_id}" =~ ^scx_ ]]; then
    CHECK_DETAIL="legacy_invalid_file_id"
    return 1
  fi

  local status_code
  status_code="$(curl -sS -o "${status_json}" -w "%{http_code}" \
    -H "Authorization: Bearer ${token}" \
    "https://stellcodex.com/api/v1/files/${file_id}/status" || true)"
  local state
  state="$(extract_status_value "${status_json}")"
  echo "F.status_http=${status_code}"
  echo "F.status_value=${state:-<none>}"

  if [[ "${status_code}" != "200" ]]; then
    CHECK_DETAIL="legacy_status_http=${status_code}"
    return 1
  fi

  CHECK_DETAIL="field=${field_used} file_id=${file_id} status_http=200"
  return 0
}

echo "# external context checks"
date -Iseconds

SAMPLE_FILE="$(find_sample_file || true)"
if [[ -z "${SAMPLE_FILE}" ]]; then
  echo "sample_file=<missing>"
  CHECK_DETAIL="sample_file_missing"
  record_result "E" "FAIL" "${CHECK_DETAIL}"
  record_result "F" "FAIL" "${CHECK_DETAIL}"
  run_check "A" check_a_headers
  run_check "B" check_b_public_health
  run_check "C" check_c_local_health
  run_check "D" check_d_dns_hosts
else
  echo "sample_file=${SAMPLE_FILE}"
  run_check "A" check_a_headers
  run_check "B" check_b_public_health
  run_check "C" check_c_local_health
  run_check "D" check_d_dns_hosts
  run_check "E" canonical_upload_flow "${SAMPLE_FILE}"
  run_check "F" legacy_upload_flow "${SAMPLE_FILE}"
fi

echo ""
echo "SUMMARY: pass=${PASS_COUNT} fail=${FAIL_COUNT} total=$((PASS_COUNT + FAIL_COUNT))"
if (( FAIL_COUNT > 0 )); then
  printf 'FAIL_ITEMS:\n'
  for item in "${FAIL_ITEMS[@]}"; do
    echo "- ${item}"
  done
  echo "RESULT=FAIL"
  exit 1
fi

echo "RESULT=PASS"
exit 0
