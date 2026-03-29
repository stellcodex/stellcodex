#!/usr/bin/env bash
# STELLCODEX V10 — Preflight Context Guard
# Run before any execution. Assert CONTEXT_OK=1.

set -euo pipefail

REPO_ROOT="/root/workspace"
FAIL=0

echo "============================================"
echo "  STELLCODEX V10 — PREFLIGHT CONTEXT GUARD"
echo "============================================"

# 1. Repo path exists
if [ -d "$REPO_ROOT" ]; then
  echo "[OK] repo_root exists: $REPO_ROOT"
else
  echo "[FAIL] repo_root missing: $REPO_ROOT"
  FAIL=1
fi

# 2. SYSTEM_STATE.json exists
if [ -f "$REPO_ROOT/SYSTEM_STATE.json" ]; then
  echo "[OK] SYSTEM_STATE.json present"
else
  echo "[FAIL] SYSTEM_STATE.json MISSING"
  FAIL=1
fi

# 3. START_HERE exists
if [ -f "$REPO_ROOT/START_HERE_STELLCODEX_V10.md" ]; then
  echo "[OK] START_HERE_STELLCODEX_V10.md present"
else
  echo "[FAIL] START_HERE_STELLCODEX_V10.md MISSING"
  FAIL=1
fi

# 4. current_phase == SELF_LEARNING_ACTIVE
PHASE=$(jq -r '.current_phase' "$REPO_ROOT/SYSTEM_STATE.json" 2>/dev/null || echo "UNKNOWN")
if [ "$PHASE" = "SELF_LEARNING_ACTIVE" ]; then
  echo "[OK] current_phase = SELF_LEARNING_ACTIVE"
else
  echo "[FAIL] current_phase = $PHASE (expected SELF_LEARNING_ACTIVE)"
  FAIL=1
fi

# 5. forbidden_reopen exists and non-empty
FORBIDDEN_LEN=$(jq '.forbidden_reopen | length' "$REPO_ROOT/SYSTEM_STATE.json" 2>/dev/null || echo "0")
if [ "$FORBIDDEN_LEN" -gt 0 ]; then
  echo "[OK] forbidden_reopen has $FORBIDDEN_LEN entries"
else
  echo "[FAIL] forbidden_reopen is empty or missing"
  FAIL=1
fi

# 6. Backend health
HEALTH=$(curl -s --max-time 5 http://127.0.0.1:8000/api/v1/health 2>/dev/null || echo "{}")
HEALTH_STATUS=$(echo "$HEALTH" | jq -r '.status' 2>/dev/null || echo "fail")
if [ "$HEALTH_STATUS" = "ok" ]; then
  echo "[OK] backend health = ok"
else
  echo "[FAIL] backend health = $HEALTH_STATUS"
  FAIL=1
fi

# 7. AI health
AI_HEALTH=$(curl -s --max-time 5 http://127.0.0.1:8000/api/v1/stell/health 2>/dev/null || echo "{}")
AI_STATUS=$(echo "$AI_HEALTH" | jq -r '.status' 2>/dev/null || echo "fail")
if [ "$AI_STATUS" = "ok" ]; then
  echo "[OK] stell-ai health = ok"
else
  echo "[FAIL] stell-ai health = $AI_STATUS"
  FAIL=1
fi

echo "--------------------------------------------"
if [ "$FAIL" -eq 0 ]; then
  echo "CONTEXT_OK=1"
  echo "All checks passed. Safe to proceed."
  exit 0
else
  echo "CONTEXT_FAIL=1"
  echo "One or more checks failed. DO NOT PROCEED."
  exit 1
fi
