#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
FORBIDDEN_REGEX='storage_key|s3://|r2://|bucket|revision_id'
TARGETS=(
  docs/contracts
  schemas
)

SCAN_TARGETS=()
for target in "${TARGETS[@]}"; do
  candidate="${ROOT%/}/${target}"
  if [ -e "$candidate" ]; then
    SCAN_TARGETS+=("$candidate")
  fi
done

echo "Scanning public contract paths for forbidden tokens: $FORBIDDEN_REGEX"
if [ "${#SCAN_TARGETS[@]}" -eq 0 ]; then
  echo "SKIP: no public contract paths found (${TARGETS[*]})"
  exit 0
fi

if grep -RInE "$FORBIDDEN_REGEX" "${SCAN_TARGETS[@]}" --exclude-dir=.git --exclude=*.zip --exclude=*.gz; then
  echo "FAIL: forbidden tokens found in public contract paths."
  exit 1
fi
echo "PASS: no forbidden tokens found in public contract paths"
