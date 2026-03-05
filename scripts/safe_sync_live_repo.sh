#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="${REPO_DIR:-/var/www/stellcodex}"
REMOTE_URL="${REMOTE_URL:-https://github.com/stellcodex/stellcodex.git}"
REMOTE_BRANCH="${REMOTE_BRANCH:-main}"
MODE="${1:---dry-run}"

if [ ! -d "$REPO_DIR/.git" ]; then
  echo "FAIL: repo not found: $REPO_DIR" >&2
  exit 1
fi

if [ "$MODE" != "--dry-run" ] && [ "$MODE" != "--execute" ]; then
  echo "Usage: $0 [--dry-run|--execute]" >&2
  exit 1
fi

local_head="$(git -C "$REPO_DIR" rev-parse HEAD)"
remote_head="$(gh api "repos/stellcodex/stellcodex/commits/$REMOTE_BRANCH" --jq .sha)"
status_lines="$(git -C "$REPO_DIR" status --short || true)"
timestamp="$(date -u +%Y%m%d_%H%M%S)"
stash_name="safe-sync-$timestamp"

echo "Repo: $REPO_DIR"
echo "Local HEAD: $local_head"
echo "Remote $REMOTE_BRANCH: $remote_head"
echo "Mode: $MODE"
echo
echo "Dirty status:"
if [ -n "$status_lines" ]; then
  printf '%s\n' "$status_lines"
else
  echo "(clean)"
fi
echo
echo "Planned sync:"
echo "1. git fetch $REMOTE_URL $REMOTE_BRANCH"
echo "2. git stash push -u -m $stash_name"
echo "3. git merge --ff-only FETCH_HEAD"
echo "4. git stash pop"

if [ "$MODE" = "--dry-run" ]; then
  exit 0
fi

git -C "$REPO_DIR" fetch "$REMOTE_URL" "$REMOTE_BRANCH"
git -C "$REPO_DIR" stash push -u -m "$stash_name"
git -C "$REPO_DIR" merge --ff-only FETCH_HEAD
git -C "$REPO_DIR" stash pop

echo
echo "PASS: live repo synced with stash round-trip"
