#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:3000}"
FAILURES=0

code_for() {
  local path="$1"
  curl -sS -o /dev/null -w "%{http_code}" "${BASE_URL}${path}"
}

pass() {
  printf 'PASS %s (%s)\n' "$1" "$2"
}

fail() {
  printf 'FAIL %s (%s)\n' "$1" "$2"
  FAILURES=$((FAILURES + 1))
}

check_exact() {
  local path="$1" expected="$2"
  local code
  code="$(code_for "$path")"
  if [ "$code" = "$expected" ]; then
    pass "$path" "$code"
  else
    fail "$path" "expected ${expected}, got ${code}"
  fi
}

check_any() {
  local path="$1"; shift
  local code
  code="$(code_for "$path")"
  for allowed in "$@"; do
    if [ "$code" = "$allowed" ]; then
      pass "$path" "$code"
      return 0
    fi
  done
  fail "$path" "got ${code}, allowed: $*"
}

check_api_health() {
  local code
  code="$(code_for "/api/health")"
  if [ "$code" = "404" ]; then
    printf 'WARN /api/health (%s) endpoint missing; middleware did not block /api/* allowlist check deferred to existing API routes\n' "$code"
    return 0
  fi
  if [ "$code" = "200" ] || [ "$code" = "401" ] || [ "$code" = "405" ]; then
    pass "/api/health" "$code"
    return 0
  fi
  fail "/api/health" "unexpected ${code}"
}

check_not_404() {
  local path="$1"
  local code
  code="$(code_for "$path")"
  if [ "$code" = "404" ]; then
    fail "$path" "404 (allowlist/middleware blocked)"
  else
    pass "$path" "$code"
  fi
}

check_exact "/" "200"
check_any "/view" "200" "307" "308"
check_any "/share" "200" "307" "308"
check_any "/admin" "200" "302" "307" "308" "401"
check_api_health
check_exact "/robots.txt" "200"
check_not_404 "/api/projects/default"

if [ "$FAILURES" -gt 0 ]; then
  echo "route-allowlist-smoke: FAIL (${FAILURES})"
  exit 1
fi

echo "route-allowlist-smoke: PASS"

