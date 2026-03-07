#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

require_cmd curl
require_cmd jq
wait_backend

SMOKE_DIR="${EVIDENCE_DIR}/smoke"
mkdir -p "${SMOKE_DIR}"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

SAMPLE_STEP="${TMP_DIR}/sample.step"
cat > "${SAMPLE_STEP}" <<'STEP'
ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('STEP AP214'),'1');
FILE_NAME('sample.step','2026-03-05T00:00:00',('STELLCODEX'),('STELLCODEX'),'','','');
FILE_SCHEMA(('AUTOMOTIVE_DESIGN'));
ENDSEC;
DATA;
#1=CARTESIAN_POINT('',(0.,0.,0.));
#2=DIRECTION('',(0.,0.,1.));
#3=DIRECTION('',(1.,0.,0.));
#4=AXIS2_PLACEMENT_3D('',#1,#2,#3);
#5=ADVANCED_BREP_SHAPE_REPRESENTATION('',(),#4);
ENDSEC;
END-ISO-10303-21;
STEP

TOKEN_RAW="${TMP_DIR}/token_raw.json"
curl -sS -X POST "${API_BASE}/auth/guest" > "${TOKEN_RAW}"
write_json_pretty "${TOKEN_RAW}" "${SMOKE_DIR}/auth_guest.json"
TOKEN="$(jq -r '.access_token' "${TOKEN_RAW}")"
if [[ -z "${TOKEN}" || "${TOKEN}" == "null" ]]; then
  echo "guest token creation failed" >&2
  exit 1
fi
AUTH_HEADER=( -H "Authorization: Bearer ${TOKEN}" )

CANONICAL_RAW="${TMP_DIR}/upload_canonical_raw.json"
curl -sS "${AUTH_HEADER[@]}" \
  -F "upload=@${SAMPLE_STEP};type=application/step" \
  "${API_BASE}/files/upload" > "${CANONICAL_RAW}"
write_json_pretty "${CANONICAL_RAW}" "${SMOKE_DIR}/upload_canonical.json"
CANONICAL_FILE_ID="$(jq -r '.file_id' "${CANONICAL_RAW}")"
if [[ -z "${CANONICAL_FILE_ID}" || "${CANONICAL_FILE_ID}" == "null" ]]; then
  echo "canonical upload failed" >&2
  exit 1
fi

LEGACY_RAW="${TMP_DIR}/upload_legacy_raw.json"
curl -sS "${AUTH_HEADER[@]}" \
  -F "file=@${SAMPLE_STEP};type=application/step" \
  "${API_BASE}/upload" > "${LEGACY_RAW}"
write_json_pretty "${LEGACY_RAW}" "${SMOKE_DIR}/upload_legacy_alias.json"
LEGACY_FILE_ID="$(jq -r '.file_id' "${LEGACY_RAW}")"
if [[ -z "${LEGACY_FILE_ID}" || "${LEGACY_FILE_ID}" == "null" ]]; then
  echo "legacy alias upload failed" >&2
  exit 1
fi

STATUS_RAW="${TMP_DIR}/status_raw.json"
READY_STATE=""
for _ in $(seq 1 120); do
  curl -sS "${AUTH_HEADER[@]}" "${API_BASE}/files/${CANONICAL_FILE_ID}/status" > "${STATUS_RAW}"
  READY_STATE="$(jq -r '.state // empty' "${STATUS_RAW}")"
  if [[ "${READY_STATE}" == "succeeded" ]]; then
    break
  fi
  if [[ "${READY_STATE}" == "failed" ]]; then
    echo "upload pipeline failed before ready" >&2
    write_json_pretty "${STATUS_RAW}" "${SMOKE_DIR}/status_last.json"
    exit 1
  fi
  sleep 2
done
write_json_pretty "${STATUS_RAW}" "${SMOKE_DIR}/status_last.json"
if [[ "${READY_STATE}" != "succeeded" ]]; then
  echo "upload did not reach succeeded state in time" >&2
  exit 1
fi

FILE_RAW="${TMP_DIR}/file_raw.json"
curl -sS "${AUTH_HEADER[@]}" "${API_BASE}/files/${CANONICAL_FILE_ID}" > "${FILE_RAW}"
write_json_pretty "${FILE_RAW}" "${SMOKE_DIR}/file_detail.json"
FILE_STATUS="$(jq -r '.status // empty' "${FILE_RAW}")"
if [[ "${FILE_STATUS}" != "ready" ]]; then
  echo "file status is not ready (${FILE_STATUS})" >&2
  exit 1
fi

MANIFEST_RAW="${TMP_DIR}/manifest_raw.json"
curl -sS "${AUTH_HEADER[@]}" "${API_BASE}/files/${CANONICAL_FILE_ID}/manifest" > "${MANIFEST_RAW}"
write_json_pretty "${MANIFEST_RAW}" "${SMOKE_DIR}/manifest.json"
if ! jq -e '.assembly_tree | type=="array" and length > 0 and all(.[]; (.occurrence_id|type=="string" and length > 0))' "${MANIFEST_RAW}" >/dev/null; then
  echo "assembly_meta/occurrence_id contract failed" >&2
  exit 1
fi
if ! jq -e '.preview_urls | type=="array" and length >= 3' "${FILE_RAW}" >/dev/null; then
  echo "ready 3D preview contract failed (expected >=3 previews)" >&2
  exit 1
fi

DECISION_RAW="${TMP_DIR}/decision_raw.json"
curl -sS "${AUTH_HEADER[@]}" "${API_BASE}/files/${CANONICAL_FILE_ID}/decision_json" > "${DECISION_RAW}"
write_json_pretty "${DECISION_RAW}" "${SMOKE_DIR}/decision_json.json"
if ! jq -e '.decision_json.state_code? // .state_code | type=="string" and length > 0' "${DECISION_RAW}" >/dev/null; then
  echo "decision_json contract failed" >&2
  exit 1
fi

ORCH_RAW="${TMP_DIR}/orchestrator_raw.json"
curl -sS "${AUTH_HEADER[@]}" "${API_BASE}/orchestrator/sessions/${CANONICAL_FILE_ID}" > "${ORCH_RAW}"
write_json_pretty "${ORCH_RAW}" "${SMOKE_DIR}/orchestrator_session.json"
if ! jq -e '.state_code | type=="string" and length > 0' "${ORCH_RAW}" >/dev/null; then
  echo "orchestrator session contract failed" >&2
  exit 1
fi

QUOTE_RAW="${TMP_DIR}/quote_raw.json"
curl -sS "${AUTH_HEADER[@]}" \
  -H "Content-Type: application/json" \
  -d "{\"file_id\":\"${CANONICAL_FILE_ID}\",\"quantities\":[1,5,10],\"material_id\":\"steel_1018\"}" \
  "${API_BASE}/quotes/generate" > "${QUOTE_RAW}"
write_json_pretty "${QUOTE_RAW}" "${SMOKE_DIR}/dfm_quote_report.json"
if ! jq -e '.quote_id | type=="string" and length > 0' "${QUOTE_RAW}" >/dev/null; then
  echo "dfm report (quote generate) failed" >&2
  exit 1
fi

SHARE_RAW="${TMP_DIR}/share_raw.json"
curl -sS "${AUTH_HEADER[@]}" \
  -H "Content-Type: application/json" \
  -d '{"permission":"download","expires_in_seconds":120}' \
  "${API_BASE}/files/${CANONICAL_FILE_ID}/share" > "${SHARE_RAW}"
write_json_pretty "${SHARE_RAW}" "${SMOKE_DIR}/share_create.json"
SHARE_TOKEN="$(jq -r '.token' "${SHARE_RAW}")"
SHARE_ID="$(jq -r '.id' "${SHARE_RAW}")"
if [[ -z "${SHARE_TOKEN}" || "${SHARE_TOKEN}" == "null" ]]; then
  echo "share creation failed" >&2
  exit 1
fi

SHARE_RESOLVE_BODY="${SMOKE_DIR}/share_resolve.json"
SHARE_RESOLVE_CODE="$(curl -sS -o "${SHARE_RESOLVE_BODY}" -w '%{http_code}' "${API_ORIGIN}/s/${SHARE_TOKEN}")"
if [[ "${SHARE_RESOLVE_CODE}" != "200" ]]; then
  echo "share resolve failed with HTTP ${SHARE_RESOLVE_CODE}" >&2
  exit 1
fi

EXPIRED_RAW="${TMP_DIR}/share_expired_raw.json"
curl -sS "${AUTH_HEADER[@]}" \
  -H "Content-Type: application/json" \
  -d '{"permission":"view","expires_in_seconds":120}' \
  "${API_BASE}/files/${CANONICAL_FILE_ID}/share" > "${EXPIRED_RAW}"
EXPIRED_TOKEN="$(jq -r '.token' "${EXPIRED_RAW}")"
EXPIRED_ID="$(jq -r '.id' "${EXPIRED_RAW}")"
compose exec -T postgres psql -U stellcodex -d stellcodex -c "UPDATE shares SET expires_at = NOW() - INTERVAL '5 minutes' WHERE id = '${EXPIRED_ID}';" >/dev/null
SHARE_410_BODY="${SMOKE_DIR}/share_expired_410.json"
SHARE_410_CODE="$(curl -sS -o "${SHARE_410_BODY}" -w '%{http_code}' "${API_ORIGIN}/s/${EXPIRED_TOKEN}")"
if [[ "${SHARE_410_CODE}" != "410" ]]; then
  echo "share expire contract failed (expected 410 got ${SHARE_410_CODE})" >&2
  exit 1
fi

RATE_RAW="${TMP_DIR}/share_rate_raw.json"
curl -sS "${AUTH_HEADER[@]}" \
  -H "Content-Type: application/json" \
  -d '{"permission":"view","expires_in_seconds":120}' \
  "${API_BASE}/files/${CANONICAL_FILE_ID}/share" > "${RATE_RAW}"
RATE_TOKEN="$(jq -r '.token' "${RATE_RAW}")"
RATE_ID="$(jq -r '.id' "${RATE_RAW}")"
WINDOW_BUCKET="$(( $(date -u +%s) / 60 ))"
RATE_KEY="stell:share:rate:${RATE_ID}:9.9.9.9:${WINDOW_BUCKET}"
compose exec -T redis redis-cli SET "${RATE_KEY}" 121 >/dev/null
compose exec -T redis redis-cli EXPIRE "${RATE_KEY}" 120 >/dev/null
SHARE_429_BODY="${SMOKE_DIR}/share_rate_429.json"
SHARE_429_CODE="$(curl -sS -o "${SHARE_429_BODY}" -w '%{http_code}' -H 'X-Forwarded-For: 9.9.9.9' "${API_ORIGIN}/s/${RATE_TOKEN}")"
if [[ "${SHARE_429_CODE}" != "429" ]]; then
  echo "share rate-limit contract failed (expected 429 got ${SHARE_429_CODE})" >&2
  exit 1
fi

AUDIT_FILE="${SMOKE_DIR}/audit_events_share.txt"
compose exec -T postgres psql -U stellcodex -d stellcodex -P pager=off -c \
  "SELECT event_type, COUNT(*) FROM audit_events WHERE event_type LIKE 'share.%' GROUP BY event_type ORDER BY event_type;" \
  > "${AUDIT_FILE}"
AUDIT_COUNT="$(compose exec -T postgres psql -U stellcodex -d stellcodex -Atc "SELECT COUNT(*) FROM audit_events WHERE event_type IN ('share.created','share.resolved','share.access_denied','share.rate_limited');")"
if [[ -z "${AUDIT_COUNT}" || "${AUDIT_COUNT}" == "0" ]]; then
  echo "audit contract failed (no share audit events found)" >&2
  exit 1
fi

cat > "${SMOKE_DIR}/summary.json" <<JSON
{
  "canonical_file_id": "${CANONICAL_FILE_ID}",
  "legacy_file_id": "${LEGACY_FILE_ID}",
  "share_id": "${SHARE_ID}",
  "share_resolve_http": ${SHARE_RESOLVE_CODE},
  "share_expire_http": ${SHARE_410_CODE},
  "share_rate_limit_http": ${SHARE_429_CODE},
  "audit_count": ${AUDIT_COUNT}
}
JSON

echo "[smoke] passed" | tee "${SMOKE_DIR}/status.txt"
