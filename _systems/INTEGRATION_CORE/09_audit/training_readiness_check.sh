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
  "$PY_BIN" -c "import importlib.util,sys;sys.exit(0 if importlib.util.find_spec('${mod}') else 1)" >/dev/null 2>&1 || {
    rag_ok="false"
    missing_modules="${missing_modules}${mod} "
  }
done

rag_runtime_ok="true"
runtime_warnings=""
for mod in chromadb langgraph; do
  timeout 20s "$PY_BIN" -c "import ${mod}" >/dev/null 2>&1 || {
    rag_runtime_ok="false"
    runtime_warnings="${runtime_warnings}${mod} "
  }
done

queue_ok="false"
if docker exec deploy_redis_1 redis-cli ping >/dev/null 2>&1; then
  queue_ok="true"
fi

github_ok="false"
if git -C /root/workspace remote get-url origin >/dev/null 2>&1; then
  github_ok="true"
fi

gdrive_ok="false"
if command -v rclone >/dev/null 2>&1; then
  remotes="$(rclone listremotes 2>/dev/null || true)"
  if printf '%s\n' "$remotes" | tr -d '\r' | grep -Eq '^(stellstorage:|gdrive:)$'; then
    gdrive_ok="true"
  fi
fi

object_storage_ok="false"
if docker ps --format '{{.Names}}' | grep -q '^deploy_minio_1$'; then
  object_storage_ok="true"
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
if [[ "$github_ok" == "true" && "$gdrive_ok" == "true" && "$object_storage_ok" == "true" && "$queue_ok" == "true" ]]; then
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
check_bool "RAG runtime smoke (chromadb/langgraph)" "$rag_runtime_ok"
if [[ "$rag_runtime_ok" == "false" ]]; then
  check_bool "RAG runtime warnings" "${runtime_warnings%% }"
fi
check_bool "dataset directories prepared" "$is_dir_set"
check_bool "ORCHESTRA queue healthy" "$queue_ok"
check_bool "external connectors verified" "$external_ok"
check_bool "required connectors (github/drive/object_storage/queue)" "$github_ok/$gdrive_ok/$object_storage_ok/$queue_ok"
check_bool "optional connector cloudflare token" "$cloudflare_ok"
check_bool "optional connector vercel token" "$vercel_ok"
check_bool "backup chain valid" "$backup_ok"
echo >> "$OUT"
echo "SYSTEM_STATUS = ${system_status}" >> "$OUT"

echo "training_readiness_report=$OUT"
