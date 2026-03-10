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

SAMPLE_GLTF="${TMP_DIR}/sample.gltf"
cat > "${SAMPLE_GLTF}" <<'GLTF'
{
  "asset": { "version": "2.0" },
  "scenes": [ { "nodes": [0] } ],
  "nodes": [ {} ],
  "scene": 0
}
GLTF

USER_EMAIL="smoke.$(date -u +%s).$RANDOM@example.com"
USER_PASSWORD="SmokePass!123"
REGISTER_RAW="${TMP_DIR}/register_raw.json"
REGISTER_PAYLOAD="$(jq -nc --arg email "${USER_EMAIL}" --arg password "${USER_PASSWORD}" '{email:$email,password:$password}')"
curl -sS \
  -H "Content-Type: application/json" \
  -d "${REGISTER_PAYLOAD}" \
  "${API_BASE}/auth/register" > "${REGISTER_RAW}"
write_json_pretty "${REGISTER_RAW}" "${SMOKE_DIR}/auth_register.json"
TOKEN="$(jq -r '.access_token' "${REGISTER_RAW}")"
if [[ -z "${TOKEN}" || "${TOKEN}" == "null" ]]; then
  echo "user register/login failed" >&2
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

VISUAL_RAW="${TMP_DIR}/upload_visual_raw.json"
curl -sS "${AUTH_HEADER[@]}" \
  -F "upload=@${SAMPLE_GLTF};type=model/gltf+json" \
  "${API_BASE}/files/upload" > "${VISUAL_RAW}"
write_json_pretty "${VISUAL_RAW}" "${SMOKE_DIR}/upload_visual.json"
VISUAL_FILE_ID="$(jq -r '.file_id' "${VISUAL_RAW}")"
if [[ -z "${VISUAL_FILE_ID}" || "${VISUAL_FILE_ID}" == "null" ]]; then
  echo "visual upload failed" >&2
  exit 1
fi

wait_for_succeeded() {
  local file_id="$1"
  local out_path="$2"
  local state=""
  for _ in $(seq 1 120); do
    curl -sS "${AUTH_HEADER[@]}" "${API_BASE}/files/${file_id}/status" > "${out_path}"
    state="$(jq -r '.state // empty' "${out_path}")"
    if [[ "${state}" == "succeeded" ]]; then
      return 0
    fi
    if [[ "${state}" == "failed" ]]; then
      return 1
    fi
    sleep 2
  done
  return 1
}

CANONICAL_STATUS_RAW="${TMP_DIR}/status_canonical_raw.json"
if ! wait_for_succeeded "${CANONICAL_FILE_ID}" "${CANONICAL_STATUS_RAW}"; then
  write_json_pretty "${CANONICAL_STATUS_RAW}" "${SMOKE_DIR}/status_canonical_last.json"
  echo "canonical upload did not reach succeeded state" >&2
  exit 1
fi
write_json_pretty "${CANONICAL_STATUS_RAW}" "${SMOKE_DIR}/status_canonical_last.json"

LEGACY_STATUS_RAW="${TMP_DIR}/status_legacy_raw.json"
if ! wait_for_succeeded "${LEGACY_FILE_ID}" "${LEGACY_STATUS_RAW}"; then
  write_json_pretty "${LEGACY_STATUS_RAW}" "${SMOKE_DIR}/status_legacy_last.json"
  echo "legacy upload did not reach succeeded state" >&2
  exit 1
fi
write_json_pretty "${LEGACY_STATUS_RAW}" "${SMOKE_DIR}/status_legacy_last.json"

VISUAL_STATUS_RAW="${TMP_DIR}/status_visual_raw.json"
if ! wait_for_succeeded "${VISUAL_FILE_ID}" "${VISUAL_STATUS_RAW}"; then
  write_json_pretty "${VISUAL_STATUS_RAW}" "${SMOKE_DIR}/status_visual_last.json"
  echo "visual upload did not reach succeeded state" >&2
  exit 1
fi
write_json_pretty "${VISUAL_STATUS_RAW}" "${SMOKE_DIR}/status_visual_last.json"

FILE_RAW="${TMP_DIR}/file_raw.json"
curl -sS "${AUTH_HEADER[@]}" "${API_BASE}/files/${CANONICAL_FILE_ID}" > "${FILE_RAW}"
write_json_pretty "${FILE_RAW}" "${SMOKE_DIR}/file_detail.json"
if ! jq -e '.file_id | type=="string" and (startswith("scx_file_") or startswith("scx_"))' "${FILE_RAW}" >/dev/null; then
  echo "file route contract failed: file_id missing/invalid" >&2
  exit 1
fi
if ! jq -e '.status=="ready"' "${FILE_RAW}" >/dev/null; then
  echo "file detail is not ready" >&2
  exit 1
fi

MANIFEST_RAW="${TMP_DIR}/manifest_raw.json"
curl -sS "${AUTH_HEADER[@]}" "${API_BASE}/files/${CANONICAL_FILE_ID}/manifest" > "${MANIFEST_RAW}"
write_json_pretty "${MANIFEST_RAW}" "${SMOKE_DIR}/manifest.json"
if ! jq -e '.assembly_tree | type=="array" and length > 0 and all(.[]; (.occurrence_id|type=="string" and length>0) and (.part_id|type=="string" and length>0) and (.display_name|type=="string" and length>0))' "${MANIFEST_RAW}" >/dev/null; then
  echo "assembly_meta contract failed" >&2
  exit 1
fi
if ! jq -e '.part_count | type=="number" and . > 0' "${MANIFEST_RAW}" >/dev/null; then
  echo "manifest part_count occurrence contract failed" >&2
  exit 1
fi
if ! jq -e '.part_count == (input.part_count)' "${MANIFEST_RAW}" "${FILE_RAW}" >/dev/null 2>&1; then
  echo "file_detail part_count does not match manifest occurrence count" >&2
  exit 1
fi

DECISION_RAW="${TMP_DIR}/decision_raw.json"
curl -sS "${AUTH_HEADER[@]}" "${API_BASE}/files/${CANONICAL_FILE_ID}/decision_json" > "${DECISION_RAW}"
write_json_pretty "${DECISION_RAW}" "${SMOKE_DIR}/decision_json.json"
if ! jq -e '.rule_version|type=="string" and length>0' "${DECISION_RAW}" >/dev/null; then
  echo "decision_json missing rule_version" >&2
  exit 1
fi
if ! jq -e '.mode|type=="string" and (.=="brep" or .=="mesh_approx" or .=="visual_only")' "${DECISION_RAW}" >/dev/null; then
  echo "decision_json missing/invalid mode" >&2
  exit 1
fi
if ! jq -e '.confidence|type=="number" and .>=0 and .<=1' "${DECISION_RAW}" >/dev/null; then
  echo "decision_json missing/invalid confidence" >&2
  exit 1
fi
if ! jq -e '.manufacturing_method|type=="string" and length>0' "${DECISION_RAW}" >/dev/null; then
  echo "decision_json missing manufacturing_method" >&2
  exit 1
fi
if ! jq -e '.rule_explanations|type=="array" and length>0' "${DECISION_RAW}" >/dev/null; then
  echo "decision_json missing rule_explanations" >&2
  exit 1
fi
if ! jq -e '.conflict_flags|type=="array"' "${DECISION_RAW}" >/dev/null; then
  echo "decision_json missing conflict_flags" >&2
  exit 1
fi

DFM_RAW="${TMP_DIR}/dfm_raw.json"
curl -sS "${AUTH_HEADER[@]}" "${API_BASE}/dfm/report?file_id=${CANONICAL_FILE_ID}" > "${DFM_RAW}"
write_json_pretty "${DFM_RAW}" "${SMOKE_DIR}/dfm_report.json"
if ! jq -e '.mode|type=="string" and length>0' "${DFM_RAW}" >/dev/null; then
  echo "dfm report missing mode" >&2
  exit 1
fi
if ! jq -e '.confidence|type=="number" and .>=0 and .<=1' "${DFM_RAW}" >/dev/null; then
  echo "dfm report missing confidence" >&2
  exit 1
fi
if ! jq -e '.rule_version|type=="string" and length>0' "${DFM_RAW}" >/dev/null; then
  echo "dfm report missing rule_version" >&2
  exit 1
fi
if ! jq -e '.rule_explanations|type=="array" and length>0' "${DFM_RAW}" >/dev/null; then
  echo "dfm report missing rule_explanations" >&2
  exit 1
fi
if ! jq -e '.recommendations|type=="array" and length>0' "${DFM_RAW}" >/dev/null; then
  echo "dfm report missing recommendations" >&2
  exit 1
fi
if ! jq -e '.wall_risks|type=="array"' "${DFM_RAW}" >/dev/null; then
  echo "dfm report missing wall_risks array" >&2
  exit 1
fi
if ! jq -e '.draft_risks|type=="array"' "${DFM_RAW}" >/dev/null; then
  echo "dfm report missing draft_risks array" >&2
  exit 1
fi
if ! jq -e '.undercut_risks|type=="array"' "${DFM_RAW}" >/dev/null; then
  echo "dfm report missing undercut_risks array" >&2
  exit 1
fi
if ! jq -e '.shrinkage_warnings|type=="array"' "${DFM_RAW}" >/dev/null; then
  echo "dfm report missing shrinkage_warnings array" >&2
  exit 1
fi
DFM_PERSIST_SQL="SELECT COUNT(*) FROM uploaded_files WHERE file_id='${CANONICAL_FILE_ID}' AND jsonb_typeof(metadata::jsonb->'dfm_report_json')='object' AND jsonb_typeof(metadata::jsonb->'dfm_report_json'->'recommendations')='array';"
DFM_PERSIST_COUNT="$(compose_exec postgres psql -U stellcodex -d stellcodex -Atc "${DFM_PERSIST_SQL}")"
if [[ "${DFM_PERSIST_COUNT}" != "1" ]]; then
  echo "dfm report persistence contract failed (dfm_report_json not persisted)" >&2
  exit 1
fi

VISUAL_DECISION_RAW="${TMP_DIR}/visual_decision_raw.json"
curl -sS "${AUTH_HEADER[@]}" "${API_BASE}/files/${VISUAL_FILE_ID}/decision_json" > "${VISUAL_DECISION_RAW}"
write_json_pretty "${VISUAL_DECISION_RAW}" "${SMOKE_DIR}/visual_decision_json.json"
if ! jq -e '.approval_required==true and (.state=="S5" or .state=="S4")' "${VISUAL_DECISION_RAW}" >/dev/null; then
  echo "visual decision did not enter approval-required state (S4/S5)" >&2
  exit 1
fi

VISUAL_SESSION_RAW="${TMP_DIR}/visual_session_raw.json"
curl -sS "${AUTH_HEADER[@]}" "${API_BASE}/orchestrator/sessions/${VISUAL_FILE_ID}" > "${VISUAL_SESSION_RAW}"
write_json_pretty "${VISUAL_SESSION_RAW}" "${SMOKE_DIR}/visual_orchestrator_session.json"
SESSION_ID="$(jq -r '.session_id' "${VISUAL_SESSION_RAW}")"
if [[ -z "${SESSION_ID}" || "${SESSION_ID}" == "null" ]]; then
  echo "orchestrator session missing session_id" >&2
  exit 1
fi

APPROVAL_REJECT_BODY="${SMOKE_DIR}/approval_reject.json"
APPROVAL_REJECT_CODE="$(curl -sS -o "${APPROVAL_REJECT_BODY}" -w '%{http_code}' "${AUTH_HEADER[@]}" \
  -H "Content-Type: application/json" \
  -d '{"note":"smoke reject"}' \
  "${API_BASE}/approvals/${SESSION_ID}/reject")"
if [[ "${APPROVAL_REJECT_CODE}" != "200" ]]; then
  echo "approval reject failed (HTTP ${APPROVAL_REJECT_CODE})" >&2
  exit 1
fi
if ! jq -e '.state=="S4"' "${APPROVAL_REJECT_BODY}" >/dev/null; then
  echo "approval reject state contract failed" >&2
  exit 1
fi

APPROVAL_APPROVE_BODY="${SMOKE_DIR}/approval_approve.json"
APPROVAL_APPROVE_CODE="$(curl -sS -o "${APPROVAL_APPROVE_BODY}" -w '%{http_code}' "${AUTH_HEADER[@]}" \
  -H "Content-Type: application/json" \
  -d '{"note":"smoke approve"}' \
  "${API_BASE}/approvals/${SESSION_ID}/approve")"
if [[ "${APPROVAL_APPROVE_CODE}" != "200" ]]; then
  echo "approval approve failed (HTTP ${APPROVAL_APPROVE_CODE})" >&2
  exit 1
fi
if ! jq -e '.state=="S7" and .approval_required==false' "${APPROVAL_APPROVE_BODY}" >/dev/null; then
  echo "approval approve transition contract failed" >&2
  exit 1
fi

SESSION_DECISION_RAW="${TMP_DIR}/session_decision_raw.json"
curl -sS "${AUTH_HEADER[@]}" "${API_BASE}/orchestrator/decision?session_id=${SESSION_ID}" > "${SESSION_DECISION_RAW}"
write_json_pretty "${SESSION_DECISION_RAW}" "${SMOKE_DIR}/session_decision.json"
if ! jq -e '.state=="S7" and (.rule_version|type=="string")' "${SESSION_DECISION_RAW}" >/dev/null; then
  echo "orchestrator decision-by-session contract failed" >&2
  exit 1
fi

PROOF_UPLOAD_RAW="${TMP_DIR}/upload_state_proof_raw.json"
curl -sS "${AUTH_HEADER[@]}" \
  -F "upload=@${SAMPLE_GLTF};type=model/gltf+json" \
  "${API_BASE}/files/upload" > "${PROOF_UPLOAD_RAW}"
write_json_pretty "${PROOF_UPLOAD_RAW}" "${SMOKE_DIR}/upload_state_proof.json"
PROOF_FILE_ID="$(jq -r '.file_id' "${PROOF_UPLOAD_RAW}")"
if [[ -z "${PROOF_FILE_ID}" || "${PROOF_FILE_ID}" == "null" ]]; then
  echo "state proof upload failed" >&2
  exit 1
fi
PROOF_STATUS_RAW="${TMP_DIR}/status_state_proof_raw.json"
if ! wait_for_succeeded "${PROOF_FILE_ID}" "${PROOF_STATUS_RAW}"; then
  write_json_pretty "${PROOF_STATUS_RAW}" "${SMOKE_DIR}/status_state_proof_last.json"
  echo "state proof upload did not reach succeeded state" >&2
  exit 1
fi

set_proof_status() {
  local next_status="$1"
  compose_exec postgres psql -U stellcodex -d stellcodex -c \
    "UPDATE uploaded_files SET status='${next_status}', decision_json='{}'::jsonb, metadata=((COALESCE(metadata::jsonb,'{}'::jsonb) - 'approval_override' - 'decision_json')::json) WHERE file_id='${PROOF_FILE_ID}';
     UPDATE orchestrator_sessions SET decision_json='{}'::jsonb WHERE file_id='${PROOF_FILE_ID}';" >/dev/null
}

STATE_PROOF_SEQUENCE=()
capture_proof_state() {
  local step_name="$1"
  local expected_state="$2"
  local out_path="${SMOKE_DIR}/state_proof_${step_name}.json"
  curl -sS "${AUTH_HEADER[@]}" "${API_BASE}/orchestrator/files/${PROOF_FILE_ID}/decision_json" > "${out_path}"
  local observed_state
  observed_state="$(jq -r '.state' "${out_path}")"
  STATE_PROOF_SEQUENCE+=("${observed_state}")
  if [[ "${observed_state}" != "${expected_state}" ]]; then
    echo "state proof failed at ${step_name}: expected ${expected_state} got ${observed_state}" >&2
    exit 1
  fi
}

set_proof_status "pending"
capture_proof_state "s0_uploaded" "S0"
set_proof_status "queued"
capture_proof_state "s1_converted" "S1"
set_proof_status "converted"
capture_proof_state "s2_assembly_ready" "S2"
set_proof_status "running"
capture_proof_state "s3_analyzing" "S3"
set_proof_status "ready"
capture_proof_state "s4_dfm_ready" "S4"
set_proof_status "ready"
capture_proof_state "s5_awaiting_approval" "S5"

set_proof_manual_approval() {
  compose_exec postgres psql -U stellcodex -d stellcodex -c \
    "UPDATE uploaded_files
        SET status='ready',
            decision_json='{}'::jsonb,
            metadata = jsonb_set((COALESCE(metadata::jsonb,'{}'::jsonb) - 'decision_json'), '{approval_override}', '\"approved\"'::jsonb, true)::json
      WHERE file_id='${PROOF_FILE_ID}';
     UPDATE orchestrator_sessions
        SET decision_json='{}'::jsonb
      WHERE file_id='${PROOF_FILE_ID}';" >/dev/null
}

set_proof_manual_approval
capture_proof_state "s6_approved" "S6"
set_proof_manual_approval
capture_proof_state "s7_share_ready" "S7"
STATE_PROOF_SESSION_ID="$(jq -r '.session_id' "${SMOKE_DIR}/state_proof_s7_share_ready.json")"
STATE_SEQ_JSON="$(printf '%s\n' "${STATE_PROOF_SEQUENCE[@]}" | jq -R . | jq -s .)"
cat > "${SMOKE_DIR}/orchestrator_state_proof.json" <<JSON
{
  "proof_file_id": "${PROOF_FILE_ID}",
  "proof_session_id": "${STATE_PROOF_SESSION_ID}",
  "sequence": ${STATE_SEQ_JSON}
}
JSON

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
compose_exec postgres psql -U stellcodex -d stellcodex -c "UPDATE shares SET expires_at = NOW() - INTERVAL '5 minutes' WHERE id = '${EXPIRED_ID}';" >/dev/null
SHARE_410_BODY="${SMOKE_DIR}/share_expired_410.json"
SHARE_410_CODE="$(curl -sS -o "${SHARE_410_BODY}" -w '%{http_code}' "${API_ORIGIN}/s/${EXPIRED_TOKEN}")"
if [[ "${SHARE_410_CODE}" != "410" ]]; then
  echo "share expire contract failed (expected 410 got ${SHARE_410_CODE})" >&2
  exit 1
fi

REVOKE_RAW="${TMP_DIR}/share_revoke_raw.json"
curl -sS "${AUTH_HEADER[@]}" \
  -H "Content-Type: application/json" \
  -d '{"permission":"view","expires_in_seconds":120}' \
  "${API_BASE}/files/${CANONICAL_FILE_ID}/share" > "${REVOKE_RAW}"
REVOKE_TOKEN="$(jq -r '.token' "${REVOKE_RAW}")"
REVOKE_ID="$(jq -r '.id' "${REVOKE_RAW}")"
curl -sS "${AUTH_HEADER[@]}" -X POST "${API_BASE}/shares/${REVOKE_ID}/revoke" > "${SMOKE_DIR}/share_revoke_action.json"
SHARE_REVOKE_BODY="${SMOKE_DIR}/share_revoke_denied.json"
SHARE_REVOKE_CODE="$(curl -sS -o "${SHARE_REVOKE_BODY}" -w '%{http_code}' "${API_ORIGIN}/s/${REVOKE_TOKEN}")"
if [[ "${SHARE_REVOKE_CODE}" != "403" ]]; then
  echo "share revoke contract failed (expected 403 got ${SHARE_REVOKE_CODE})" >&2
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
# Guard against minute-boundary races: seed current and next bucket.
for BUCKET in "${WINDOW_BUCKET}" "$((WINDOW_BUCKET + 1))"; do
  RATE_KEY="stell:share:rate:${RATE_ID}:9.9.9.9:${BUCKET}"
  compose_exec redis redis-cli SET "${RATE_KEY}" 121 >/dev/null
  compose_exec redis redis-cli EXPIRE "${RATE_KEY}" 120 >/dev/null
done
SHARE_429_BODY="${SMOKE_DIR}/share_rate_429.json"
SHARE_429_CODE="$(curl -sS -o "${SHARE_429_BODY}" -w '%{http_code}' -H 'X-Forwarded-For: 9.9.9.9' "${API_ORIGIN}/s/${RATE_TOKEN}")"
if [[ "${SHARE_429_CODE}" != "429" ]]; then
  echo "share rate-limit contract failed (expected 429 got ${SHARE_429_CODE})" >&2
  exit 1
fi

INVALID_TOKEN="invalid-token-v7-proof"
INVALID_HASH="$(printf '%s' "${INVALID_TOKEN}" | sha256sum | awk '{print $1}' | cut -c1-24)"
INVALID_BUCKET="$(( $(date -u +%s) / 60 ))"
for BUCKET in "${INVALID_BUCKET}" "$((INVALID_BUCKET + 1))"; do
  INVALID_RATE_KEY="stell:share:token_probe:8.8.8.8:${INVALID_HASH}:${BUCKET}"
  compose_exec redis redis-cli SET "${INVALID_RATE_KEY}" 31 >/dev/null
  compose_exec redis redis-cli EXPIRE "${INVALID_RATE_KEY}" 120 >/dev/null
done
SHARE_INVALID_429_BODY="${SMOKE_DIR}/share_invalid_token_429.json"
SHARE_INVALID_429_CODE="$(curl -sS -o "${SHARE_INVALID_429_BODY}" -w '%{http_code}' -H 'X-Forwarded-For: 8.8.8.8' "${API_ORIGIN}/s/${INVALID_TOKEN}")"
if [[ "${SHARE_INVALID_429_CODE}" != "429" ]]; then
  echo "share brute-force token probe rate-limit failed (expected 429 got ${SHARE_INVALID_429_CODE})" >&2
  exit 1
fi

compose_exec postgres psql -U stellcodex -d stellcodex -c \
  "UPDATE uploaded_files SET metadata = ((COALESCE(metadata::jsonb,'{}'::jsonb) - 'assembly_meta_key' - 'assembly_meta')::json) WHERE file_id = '${LEGACY_FILE_ID}';" >/dev/null
BROKEN_STATUS_BODY="${SMOKE_DIR}/ready_without_assembly_status.json"
curl -sS "${AUTH_HEADER[@]}" "${API_BASE}/files/${LEGACY_FILE_ID}/status" > "${BROKEN_STATUS_BODY}"
if ! jq -e '.state=="failed"' "${BROKEN_STATUS_BODY}" >/dev/null; then
  echo "assembly_meta enforce contract failed (ready file stayed non-failed)" >&2
  exit 1
fi
BROKEN_DB_STATUS="$(compose_exec postgres psql -U stellcodex -d stellcodex -Atc "SELECT status FROM uploaded_files WHERE file_id='${LEGACY_FILE_ID}' LIMIT 1;")"
if [[ "${BROKEN_DB_STATUS}" != "failed" ]]; then
  echo "assembly_meta enforce contract failed (db status did not persist to failed)" >&2
  exit 1
fi

AUDIT_FILE="${SMOKE_DIR}/audit_events_share.txt"
compose_exec postgres psql -U stellcodex -d stellcodex -P pager=off -c \
  "SELECT event_type, COUNT(*) FROM audit_events WHERE event_type LIKE 'share.%' OR event_type LIKE 'approval.%' GROUP BY event_type ORDER BY event_type;" \
  > "${AUDIT_FILE}"
AUDIT_COUNT="$(compose_exec postgres psql -U stellcodex -d stellcodex -Atc "SELECT COUNT(*) FROM audit_events WHERE event_type IN ('share.created','share.resolved','share.access_denied','share.rate_limited','approval.approved','approval.rejected');")"
if [[ -z "${AUDIT_COUNT}" || "${AUDIT_COUNT}" == "0" ]]; then
  echo "audit contract failed (expected share/approval audit events)" >&2
  exit 1
fi

cat > "${SMOKE_DIR}/summary.json" <<JSON
{
  "canonical_file_id": "${CANONICAL_FILE_ID}",
  "legacy_file_id": "${LEGACY_FILE_ID}",
  "visual_file_id": "${VISUAL_FILE_ID}",
  "state_proof_file_id": "${PROOF_FILE_ID}",
  "state_proof_session_id": "${STATE_PROOF_SESSION_ID}",
  "state_proof_sequence": ${STATE_SEQ_JSON},
  "approval_session_id": "${SESSION_ID}",
  "approval_reject_http": ${APPROVAL_REJECT_CODE},
  "approval_approve_http": ${APPROVAL_APPROVE_CODE},
  "dfm_persist_count": ${DFM_PERSIST_COUNT},
  "share_id": "${SHARE_ID}",
  "share_resolve_http": ${SHARE_RESOLVE_CODE},
  "share_expire_http": ${SHARE_410_CODE},
  "share_revoke_http": ${SHARE_REVOKE_CODE},
  "share_rate_limit_http": ${SHARE_429_CODE},
  "share_invalid_token_rate_limit_http": ${SHARE_INVALID_429_CODE},
  "audit_count": ${AUDIT_COUNT}
}
JSON

echo "[smoke] passed" | tee "${SMOKE_DIR}/status.txt"
