#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-.}"
FORBIDDEN_REGEX='storage_key|s3://|r2://|bucket|revision_id'
echo "Scanning repo for forbidden public-contract tokens: $FORBIDDEN_REGEX"
if grep -RInE "$FORBIDDEN_REGEX" "$ROOT" --exclude-dir=.git --exclude=*.zip --exclude=*.gz ; then
  echo "FAIL: forbidden tokens found (review whether they leak to public responses)."
  exit 1
fi
echo "PASS: no forbidden tokens found"
