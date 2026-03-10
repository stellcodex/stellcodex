#!/usr/bin/env bash
set -euo pipefail

REMOTE="gdrive:"
APPLY=0
LOG_PATH=""

usage() {
  cat <<'USAGE'
Usage: drive_normalize_apply.sh [--remote gdrive:] [--apply] [--log /path/to/log.jsonl]

Default mode is dry-run. Pass --apply to execute moves.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --remote)
      REMOTE="${2:-}"
      shift 2
      ;;
    --apply)
      APPLY=1
      shift
      ;;
    --log)
      LOG_PATH="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 2
      ;;
  esac
done

if [[ -z "$REMOTE" ]]; then
  echo "--remote cannot be empty" >&2
  exit 2
fi

if [[ -z "$LOG_PATH" ]]; then
  TS="$(date -u +%Y%m%dT%H%M%SZ)"
  LOG_PATH="/root/workspace/evidence/drive_normalize_${TS}.jsonl"
fi

mkdir -p "$(dirname "$LOG_PATH")"

MODE="dry-run"
if [[ "$APPLY" -eq 1 ]]; then
  MODE="apply"
fi

if [[ "${REMOTE}" != *: ]]; then
  REMOTE="${REMOTE}:"
fi

CANONICAL_FOLDERS=(
  "STELL/00_ARCHIVE"
  "STELL/01_BACKUPS"
  "STELL/02_DATASETS"
  "STELL/03_EVIDENCE"
  "STELL/04_REPORTS"
  "STELL/05_MODEL_OUTPUTS"
  "STELL/06_COMPANY_DOCS"
  "STELL/07_EXPORTS"
  "STELL/08_STELL_AI_MEMORY"
  "STELL/09_STELLCODEX_ARTIFACTS"
  "STELL/10_ORCHESTRA_JOBS"
)

ROOT_MAPPINGS=(
  "Stell_AI_Memory|STELL/08_STELL_AI_MEMORY/legacy_Stell_AI_Memory"
  "Stellcodex_Backups|STELL/01_BACKUPS/legacy_Stellcodex_Backups"
  "stellcodex-backups|STELL/01_BACKUPS/legacy_stellcodex-backups"
  "stellcodex-archive|STELL/00_ARCHIVE/legacy_stellcodex-archive"
)

SYSTEM_CORE_MAPPINGS=(
  "STELL_SYSTEM_CORE/01_identity|STELL/06_COMPANY_DOCS/system_core/01_identity"
  "STELL_SYSTEM_CORE/02_constitution|STELL/06_COMPANY_DOCS/system_core/02_constitution"
  "STELL_SYSTEM_CORE/03_global_policies|STELL/06_COMPANY_DOCS/system_core/03_global_policies"
  "STELL_SYSTEM_CORE/04_roles|STELL/06_COMPANY_DOCS/system_core/04_roles"
  "STELL_SYSTEM_CORE/05_workers|STELL/06_COMPANY_DOCS/system_core/05_workers"
  "STELL_SYSTEM_CORE/06_tasks|STELL/10_ORCHESTRA_JOBS/system_core/06_tasks"
  "STELL_SYSTEM_CORE/07_output_contracts|STELL/06_COMPANY_DOCS/system_core/07_output_contracts"
  "STELL_SYSTEM_CORE/08_tool_policies|STELL/06_COMPANY_DOCS/system_core/08_tool_policies"
  "STELL_SYSTEM_CORE/09_legacy_archive|STELL/00_ARCHIVE/system_core/09_legacy_archive"
  "STELL_SYSTEM_CORE/10_reports|STELL/04_REPORTS/system_core/10_reports"
)

STELLCODEX_MAPPINGS=(
  "stellcodex/01_truth|STELL/06_COMPANY_DOCS/stellcodex/01_truth"
  "stellcodex/02_backups|STELL/01_BACKUPS/stellcodex/02_backups"
  "stellcodex/03_evidence|STELL/03_EVIDENCE/stellcodex/03_evidence"
  "stellcodex/04_reports|STELL/04_REPORTS/stellcodex/04_reports"
  "stellcodex/05_datasets|STELL/02_DATASETS/stellcodex/05_datasets"
  "stellcodex/06_archive|STELL/00_ARCHIVE/stellcodex/06_archive"
  "stellcodex/07_snapshots|STELL/01_BACKUPS/stellcodex/07_snapshots"
  "stellcodex/08_runtime_exports|STELL/07_EXPORTS/stellcodex/08_runtime_exports"
)

GENOIS_MAPPINGS=(
  "stellcodex-genois/01_inbox|STELL/10_ORCHESTRA_JOBS/stellcodex_genois/01_inbox"
  "stellcodex-genois/02_approved|STELL/09_STELLCODEX_ARTIFACTS/stellcodex_genois/02_approved"
  "stellcodex-genois/03_archive|STELL/00_ARCHIVE/stellcodex_genois/03_archive"
  "stellcodex-genois/04_exports|STELL/07_EXPORTS/stellcodex_genois/04_exports"
  "stellcodex-genois/05_whatsapp_ingest|STELL/10_ORCHESTRA_JOBS/stellcodex_genois/05_whatsapp_ingest"
  "stellcodex-genois/06_reports|STELL/04_REPORTS/stellcodex_genois/06_reports"
)

move_attempted=0
move_succeeded=0
move_skipped=0
move_failed=0

ts() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

json_log() {
  local status="$1"
  local source="$2"
  local target="$3"
  local reason="$4"
  printf '{"timestamp":"%s","mode":"%s","status":"%s","source":"%s","target":"%s","reason":"%s"}\n' \
    "$(ts)" "$MODE" "$status" "$source" "$target" "$reason" >> "$LOG_PATH"
}

ensure_dir() {
  local path="$1"
  rclone mkdir "${REMOTE}${path}"
}

source_exists() {
  local source="$1"
  rclone lsf "${REMOTE}${source}" --max-depth 1 >/dev/null 2>&1
}

move_mapping() {
  local source="$1"
  local target="$2"
  move_attempted=$((move_attempted + 1))

  if ! source_exists "$source"; then
    move_skipped=$((move_skipped + 1))
    json_log "skipped" "$source" "$target" "source_missing"
    return 0
  fi

  ensure_dir "$target"
  if [[ "$APPLY" -eq 1 ]]; then
    if rclone move "${REMOTE}${source}" "${REMOTE}${target}" --create-empty-src-dirs; then
      move_succeeded=$((move_succeeded + 1))
      json_log "moved" "$source" "$target" "applied"
      return 0
    fi
    move_failed=$((move_failed + 1))
    json_log "failed" "$source" "$target" "move_error"
    return 1
  fi

  if rclone move "${REMOTE}${source}" "${REMOTE}${target}" --create-empty-src-dirs --dry-run; then
    move_succeeded=$((move_succeeded + 1))
    json_log "planned" "$source" "$target" "dry_run"
    return 0
  fi

  move_failed=$((move_failed + 1))
  json_log "failed" "$source" "$target" "dry_run_error"
  return 1
}

echo "Drive normalize mode: ${MODE}"
echo "Drive normalize remote: ${REMOTE}"
echo "Drive normalize log: ${LOG_PATH}"

for folder in "${CANONICAL_FOLDERS[@]}"; do
  ensure_dir "$folder"
done

for row in "${ROOT_MAPPINGS[@]}"; do
  IFS='|' read -r source target <<< "$row"
  move_mapping "$source" "$target"
done

for row in "${SYSTEM_CORE_MAPPINGS[@]}"; do
  IFS='|' read -r source target <<< "$row"
  move_mapping "$source" "$target"
done

for row in "${STELLCODEX_MAPPINGS[@]}"; do
  IFS='|' read -r source target <<< "$row"
  move_mapping "$source" "$target"
done

for row in "${GENOIS_MAPPINGS[@]}"; do
  IFS='|' read -r source target <<< "$row"
  move_mapping "$source" "$target"
done

SUMMARY_JSON=$(printf '{"timestamp":"%s","mode":"%s","attempted":%d,"succeeded":%d,"skipped":%d,"failed":%d,"log_path":"%s"}' \
  "$(ts)" "$MODE" "$move_attempted" "$move_succeeded" "$move_skipped" "$move_failed" "$LOG_PATH")

echo "$SUMMARY_JSON"

if [[ "$move_failed" -gt 0 ]]; then
  exit 1
fi
