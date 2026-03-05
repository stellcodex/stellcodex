#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:7010}"
WORKDIR="$(cd "$(dirname "$0")" && pwd)"
CURL_MAX_TIME="${CURL_MAX_TIME:-90}"
FAILFAST_PIN='{"gemini":"acceptance_failfast","codex":"codex_executor","claude":"acceptance_failfast","abacus":"acceptance_failfast"}'

compose_cmd() {
  if docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  else
    docker-compose "$@"
  fi
}

reset_cooldown() {
  local model="$1"
  curl -sS --max-time 20 -X POST "${BASE_URL}/quota/reset" \
    -H "Content-Type: application/json" \
    -d "{\"model\":\"${model}\",\"cooldown_minutes\":120}" >/tmp/orchestra_acceptance_quota_"${model}".json
}

echo "[A] docker compose up -d --build"
compose_cmd -f "${WORKDIR}/docker-compose.yml" up -d --build >/tmp/orchestra_acceptance_up.log 2>&1
echo "  OK"

echo "[B] GET /state returns JSON"
STATE_JSON="$(curl -sS --max-time 20 "${BASE_URL}/state")"
python3 - "$STATE_JSON" <<'PY'
import json,sys
d=json.loads(sys.argv[1])
assert "deferred_count" in d
print("  OK")
PY

echo "[C] POST /orchestrate contains required fields and core roles"
for model in gemini_conductor local_reason local_fast codex_executor; do
  reset_cooldown "$model"
done
ORCH_PAYLOAD="$(printf '{"task":"acceptance smoke task","speed":"eco","pin":%s}' "${FAILFAST_PIN}")"
if ! ORCH_JSON="$(curl -sS --max-time "${CURL_MAX_TIME}" -X POST "${BASE_URL}/orchestrate" -H "Content-Type: application/json" -d "${ORCH_PAYLOAD}")"; then
  echo "  FAIL: step C /orchestrate request timed out or failed (max ${CURL_MAX_TIME}s)"
  exit 1
fi
if [[ -z "${ORCH_JSON}" ]]; then
  echo "  FAIL: step C /orchestrate returned empty response"
  exit 1
fi
python3 - "$ORCH_JSON" <<'PY'
import json,sys
d=json.loads(sys.argv[1])
assert isinstance(d.get("routing_decisions"), list)
assert isinstance(d.get("results"), list)
assert isinstance(d.get("final"), dict)
assert isinstance(d["final"].get("output"), str)
assert isinstance(d.get("deferred"), dict)
roles={r.get("role") for r in d["results"] if isinstance(r,dict)}
for required in {"gemini","codex","claude","abacus"}:
    assert required in roles, f"missing role: {required}"
print("  OK")
PY

echo "[D] Simulate cooldown defer via /quota/reset"
for model in gemini_conductor local_reason local_fast codex_executor; do
  reset_cooldown "$model"
done
DEFER_PAYLOAD="$(printf '{"task":"cooldown simulation test","speed":"eco","pin":%s}' "${FAILFAST_PIN}")"
if ! DEFER_JSON="$(curl -sS --max-time "${CURL_MAX_TIME}" -X POST "${BASE_URL}/orchestrate" -H "Content-Type: application/json" -d "${DEFER_PAYLOAD}")"; then
  echo "  FAIL: step D /orchestrate request timed out or failed (max ${CURL_MAX_TIME}s)"
  exit 1
fi
if [[ -z "${DEFER_JSON}" ]]; then
  echo "  FAIL: step D /orchestrate returned empty response"
  exit 1
fi
python3 - "$DEFER_JSON" <<'PY'
import json,sys
d=json.loads(sys.argv[1])
assert isinstance(d.get("results"), list)
assert isinstance(d.get("deferred"), dict)
assert isinstance(d.get("final"), dict)
assert isinstance(d["final"].get("output"), str)
codex=[r for r in d["results"] if isinstance(r,dict) and r.get("role")=="codex"]
assert codex, "missing codex result"
status=str(codex[0].get("status",""))
assert status.startswith("deferred_"), f"codex not deferred: {status}"
newly=d["deferred"].get("newly_deferred",[])
assert isinstance(newly,list)
assert any(item.get("model")=="codex_executor" for item in newly if isinstance(item,dict)), "codex defer summary missing"
print("  OK")
PY

echo "All acceptance checks passed."
