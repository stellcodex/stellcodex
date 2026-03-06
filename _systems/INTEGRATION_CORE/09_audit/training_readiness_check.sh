#!/usr/bin/env bash
set -euo pipefail

ROOT="/root/workspace/_systems"
DATASETS="/root/workspace/_datasets"
AUDIT_DIR="${ROOT}/audit"
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
OUT="${AUDIT_DIR}/training_readiness_${TS//[:]/_}.md"
PY_BIN="/root/workspace/AI/.venv/bin/python"

if [[ ! -x "$PY_BIN" ]]; then
  PY_BIN="python3"
fi

mkdir -p "$AUDIT_DIR"

check_bool() {
  local label="$1"
  local status="$2"
  echo "- ${label}: ${status}" >> "$OUT"
}

has_file() {
  [[ -f "$1" ]] && echo "true" || echo "false"
}

is_dir_set="true"
for d in training_raw training_clean embeddings solved_cases prompts evaluation; do
  [[ -d "${DATASETS}/${d}" ]] || is_dir_set="false"
done

rag_ok="true"
missing_modules=""
for mod in litellm langchain langgraph llama_index chromadb qdrant_client sentence_transformers rank_bm25 opentelemetry; do
  "$PY_BIN" -c "import ${mod}" >/dev/null 2>&1 || {
    rag_ok="false"
    missing_modules="${missing_modules}${mod} "
  }
done

queue_ok="false"
if docker exec deploy_redis_1 redis-cli ping >/dev/null 2>&1; then
  queue_ok="true"
fi

cloudflare_ok="false"
vercel_ok="false"
if env | grep -qE "^(CLOUDFLARE_API_TOKEN|CLOUDFLARE_TOKEN)="; then
  cloudflare_ok="true"
fi
if env | grep -q "^VERCEL_TOKEN="; then
  vercel_ok="true"
fi

external_ok="false"
if [[ "$cloudflare_ok" == "true" && "$vercel_ok" == "true" ]]; then
  external_ok="true"
fi

backup_ok="false"
if find /root/stellcodex_output/backups -maxdepth 1 -type f -name 'backup_*.zip' >/dev/null 2>&1; then
  if [[ "$(find /root/stellcodex_output/backups -maxdepth 1 -type f -name 'backup_*.zip' | wc -l | awk '{print $1}')" -gt 0 ]]; then
    backup_ok="true"
  fi
fi

stell_manifest="$(has_file "${ROOT}/STELL_CORE/ACTIVE_STELL_MANIFEST.json")"

system_status="TRAINING_NOT_READY"
if [[ "$stell_manifest" == "true" && "$rag_ok" == "true" && "$is_dir_set" == "true" && "$queue_ok" == "true" && "$external_ok" == "true" && "$backup_ok" == "true" ]]; then
  system_status="TRAINING_READY"
fi

{
  echo "# Training Readiness Check"
  echo
  echo "Generated: ${TS}"
  echo
} > "$OUT"

check_bool "STELL manifest active" "$stell_manifest"
check_bool "RAG stack installed" "$rag_ok"
if [[ "$rag_ok" == "false" ]]; then
  check_bool "RAG missing modules" "${missing_modules%% }"
  check_bool "RAG python runtime" "$PY_BIN"
fi
check_bool "dataset directories prepared" "$is_dir_set"
check_bool "ORCHESTRA queue healthy" "$queue_ok"
check_bool "external connectors verified" "$external_ok"
check_bool "backup chain valid" "$backup_ok"
echo >> "$OUT"
echo "SYSTEM_STATUS = ${system_status}" >> "$OUT"

echo "training_readiness_report=$OUT"
