#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "${ROOT_DIR}/scripts/lib/runtime_env.sh"

EVIDENCE_DIR="${ROOT_DIR}/evidence"
OUT_FILE="${EVIDENCE_DIR}/smoke_gate_output.txt"
BACKEND_BASE_URL="${BACKEND_BASE_URL:-$(runtime_resolve_backend_base_url)}"
API_BASE="${API_BASE:-${BACKEND_BASE_URL%/}/api/v1}"
FRONT_BASE="${FRONT_BASE:-$(runtime_resolve_front_base_url)}"
API_ORIGIN="${API_BASE%/api/v1}"
STEP_SAMPLE="${STEP_SAMPLE:-$(runtime_resolve_step_sample_path 2>/dev/null || true)}"
STL_SAMPLE="${STL_SAMPLE:-$(runtime_resolve_stl_sample_path 2>/dev/null || true)}"

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

echo "# V10 smoke gate"
date -Iseconds
echo "api_base=${API_BASE}"
echo "front_base=${FRONT_BASE}"

echo "[1/12] backend health"
HEALTH_CODE="$(curl -sS -o "${TMP_DIR}/health.json" -w "%{http_code}" "${API_BASE}/health" || true)"
[[ "${HEALTH_CODE}" == "200" ]] || fail "backend health http=${HEALTH_CODE}"
pass "backend health 200"

echo "[2/12] authenticated session"
TOKEN="$(runtime_request_auth_token "${API_BASE}" 2>/dev/null || true)"
[[ -n "${TOKEN}" ]] || fail "auth token unavailable"
AUTH=(-H "Authorization: Bearer ${TOKEN}")
pass "authenticated session issued"

echo "[3/12] formats registry endpoint"
FORMATS_HTTP="$(curl -sS -o "${EVIDENCE_DIR}/formats_registry_dump.json" -w "%{http_code}" "${API_BASE}/formats" || true)"
[[ "${FORMATS_HTTP}" == "200" ]] || fail "formats endpoint http=${FORMATS_HTTP}"
python3 - <<PY || fail "formats registry payload invalid"
import json
data=json.load(open("${EVIDENCE_DIR}/formats_registry_dump.json"))
assert isinstance(data.get("items"), list) and len(data["items"]) > 0
assert isinstance(data.get("groups"), dict) and "rejected" in data["groups"]
PY
pass "formats endpoint ok"

echo "[4/12] explorer endpoints baseline"
TREE_HTTP="$(curl -sS -o "${EVIDENCE_DIR}/explorer_tree.json" -w "%{http_code}" "${AUTH[@]}" "${API_BASE}/explorer/tree?project_id=default" || true)"
[[ "${TREE_HTTP}" == "200" ]] || fail "explorer tree http=${TREE_HTTP}"

LIST3D_HTTP="$(curl -sS -o "${EVIDENCE_DIR}/explorer_list_3d.json" -w "%{http_code}" "${AUTH[@]}" "${API_BASE}/explorer/list?project_id=default&filter=brep" || true)"
[[ "${LIST3D_HTTP}" == "200" ]] || fail "explorer list 3d http=${LIST3D_HTTP}"

LISTDOC_HTTP="$(curl -sS -o "${EVIDENCE_DIR}/explorer_list_docs.json" -w "%{http_code}" "${AUTH[@]}" "${API_BASE}/explorer/list?project_id=default&filter=doc" || true)"
[[ "${LISTDOC_HTTP}" == "200" ]] || fail "explorer list docs http=${LISTDOC_HTTP}"
pass "explorer endpoints 200"

create_docx_sample() {
  python3 - <<PY
import zipfile
from pathlib import Path
path=Path("${TMP_DIR}/sample.docx")
with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>""")
    z.writestr("_rels/.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>""")
    z.writestr("word/document.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>STELLCODEX DOCX smoke sample</w:t></w:r></w:p>
  </w:body>
</w:document>""")
print(path)
PY
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

[[ -f "${STEP_SAMPLE}" ]] || fail "step sample missing: ${STEP_SAMPLE}"
[[ -f "${STL_SAMPLE}" ]] || fail "stl sample missing: ${STL_SAMPLE}"
create_docx_sample >/dev/null

echo "[5/12] STEP upload -> ready -> mandatory 3D artifacts"
STEP_ID="$(upload_and_wait_ready "${STEP_SAMPLE}" "application/step" "step")" || fail "step upload/status failed"
curl -sS "${AUTH[@]}" "${API_BASE}/files/${STEP_ID}" > "${TMP_DIR}/step_detail.json" || fail "step detail failed"
python3 - <<PY || fail "step mandatory artifacts missing"
import json
d=json.load(open("${TMP_DIR}/step_detail.json"))
assert d.get("mode") == "brep", d.get("mode")
assert isinstance(d.get("preview_urls"), list) and len(d["preview_urls"]) >= 3
b=d.get("bbox_meta") or {}
assert all(k in b for k in ("x","y","z")), b
assert d.get("part_count") is not None
PY
STEP_PREVIEW="$(python3 - <<PY
import json
d=json.load(open("${TMP_DIR}/step_detail.json"))
print((d.get("preview_urls") or [""])[0])
PY
)"
[[ -n "${STEP_PREVIEW}" ]] || fail "step preview url empty"
curl -sS -D "${EVIDENCE_DIR}/3d_preview_fetch.txt" -o /dev/null "${AUTH[@]}" "${API_ORIGIN}${STEP_PREVIEW}" || fail "step preview fetch failed"
grep -q "200" "${EVIDENCE_DIR}/3d_preview_fetch.txt" || fail "step preview not 200"
pass "step contract ok"

echo "[6/12] STL upload -> mode mesh_approx + preview jpg"
STL_ID="$(upload_and_wait_ready "${STL_SAMPLE}" "model/stl" "stl")" || fail "stl upload/status failed"
curl -sS "${AUTH[@]}" "${API_BASE}/files/${STL_ID}" > "${TMP_DIR}/stl_detail.json" || fail "stl detail failed"
python3 - <<PY || fail "stl contract invalid"
import json
d=json.load(open("${TMP_DIR}/stl_detail.json"))
assert d.get("mode") == "mesh_approx", d.get("mode")
assert isinstance(d.get("preview_urls"), list) and len(d["preview_urls"]) >= 3
PY
pass "stl contract ok"

echo "[7/12] DOCX upload -> ready -> pdf + thumb"
DOCX_ID="$(upload_and_wait_ready "${TMP_DIR}/sample.docx" "application/vnd.openxmlformats-officedocument.wordprocessingml.document" "docx")" || fail "docx upload/status failed"
curl -sS "${AUTH[@]}" "${API_BASE}/files/${DOCX_ID}" > "${TMP_DIR}/docx_detail.json" || fail "docx detail failed"
python3 - <<PY || fail "docx contract invalid"
import json
d=json.load(open("${TMP_DIR}/docx_detail.json"))
assert d.get("kind") == "doc", d.get("kind")
assert isinstance(d.get("thumbnail_url"), str) and d["thumbnail_url"]
assert isinstance(d.get("preview_urls"), list) and len(d["preview_urls"]) >= 1
PY
DOC_PDF="$(python3 - <<PY
import json
d=json.load(open("${TMP_DIR}/docx_detail.json"))
urls=d.get("preview_urls") or []
print(urls[0] if urls else "")
PY
)"
[[ -n "${DOC_PDF}" ]] || fail "docx preview pdf missing"
DOC_PDF_HTTP="$(curl -sS -o /dev/null -w "%{http_code}" "${AUTH[@]}" "${API_ORIGIN}${DOC_PDF}" || true)"
[[ "${DOC_PDF_HTTP}" == "200" ]] || fail "docx pdf preview http=${DOC_PDF_HTTP}"
pass "docx contract ok"

echo "[8/12] explorer evidence after uploads"
curl -sS "${AUTH[@]}" "${API_BASE}/explorer/tree?project_id=default" > "${EVIDENCE_DIR}/explorer_tree.json" || fail "explorer tree evidence failed"
curl -sS "${AUTH[@]}" "${API_BASE}/explorer/list?project_id=default&filter=brep" > "${EVIDENCE_DIR}/explorer_list_3d.json" || fail "explorer list 3d evidence failed"
curl -sS "${AUTH[@]}" "${API_BASE}/explorer/list?project_id=default&filter=doc" > "${EVIDENCE_DIR}/explorer_list_docs.json" || fail "explorer list docs evidence failed"
pass "explorer evidence captured"

echo "[9/12] share routes"
curl -sS -X POST "${AUTH[@]}" -H "Content-Type: application/json" -d '{}' \
  "${API_BASE}/files/${STEP_ID}/share" > "${TMP_DIR}/share_create.json" || fail "share create failed"
SHARE_TOKEN="$(parse_json_field "${TMP_DIR}/share_create.json" "token")"
[[ -n "${SHARE_TOKEN}" ]] || fail "share token empty"

SHARE_RESOLVE_HTTP="$(curl -sS -o "${TMP_DIR}/share_resolve.json" -w "%{http_code}" "${API_BASE}/shares/${SHARE_TOKEN}" || true)"
[[ "${SHARE_RESOLVE_HTTP}" == "200" ]] || fail "share resolve http=${SHARE_RESOLVE_HTTP}"

S_ROUTE_HTTP="$(curl -sS -o /dev/null -w "%{http_code}" "${FRONT_BASE}/s/${SHARE_TOKEN}" || true)"
SHARE_ROUTE_HTTP="$(curl -sS -o /dev/null -w "%{http_code}" "${FRONT_BASE}/share/${SHARE_TOKEN}" || true)"
[[ "${S_ROUTE_HTTP}" != "404" ]] || fail "/s/{token} route returned 404"
[[ "${SHARE_ROUTE_HTTP}" != "404" ]] || fail "/share/{token} route returned 404"
pass "share routes non-404"

echo "[10/12] leak check (public JSON payloads)"
FORBIDDEN_REGEX='storage_key|s3://|r2://|bucket|revision_id'
cat \
  "${EVIDENCE_DIR}/formats_registry_dump.json" \
  "${EVIDENCE_DIR}/explorer_tree.json" \
  "${EVIDENCE_DIR}/explorer_list_3d.json" \
  "${EVIDENCE_DIR}/explorer_list_docs.json" \
  "${TMP_DIR}/step_detail.json" \
  "${TMP_DIR}/stl_detail.json" \
  "${TMP_DIR}/docx_detail.json" \
  "${TMP_DIR}/share_resolve.json" \
  > "${TMP_DIR}/public_payloads.json"

if grep -Eni "${FORBIDDEN_REGEX}" "${TMP_DIR}/public_payloads.json" > "${EVIDENCE_DIR}/leak_check.txt"; then
  fail "public payload leak check failed"
fi
echo "PASS: no forbidden token leak in public payloads" > "${EVIDENCE_DIR}/leak_check.txt"
pass "leak check ok"

echo "[11/12] summary IDs"
echo "step_id=${STEP_ID}"
echo "stl_id=${STL_ID}"
echo "docx_id=${DOCX_ID}"
echo "share_token=${SHARE_TOKEN}"
pass "summary captured"

echo "[12/12] final result"
echo "RESULT=PASS"
echo "EVIDENCE=${OUT_FILE}"
