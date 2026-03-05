#!/bin/bash
# Kesinti dayanikli checkpoint kayit scripti
# Kullanim:
#   bash session-save.sh "codex" "Yapilan isin ozeti"
#   bash session-save.sh "codex" "Yapilan isin ozeti" "siradaki adim"

set -euo pipefail

AI_NAME="${1:-unknown}"
SUMMARY="${2:-Ozet girilmedi}"
NEXT_STEP="${3:-}"
SCRIPT="/root/workspace/scripts/progress_checkpoint.py"

python3 "$SCRIPT" \
  --agent "$AI_NAME" \
  --task "manual-session-save" \
  --status "checkpointed" \
  --summary "$SUMMARY" \
  --next-step "$NEXT_STEP"

echo "Session checkpoint yazildi."
