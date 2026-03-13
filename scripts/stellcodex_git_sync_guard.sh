#!/usr/bin/env bash
set -euo pipefail

ROOT="/root/workspace"
source "${ROOT}/scripts/stellcodex_lock.sh"
REPO_DIR="${REPO_DIR:-${ROOT}}"
REMOTE_NAME="${REMOTE_NAME:-origin}"
REMOTE_BASE="${REMOTE_BASE:-gdrive:stellcodex}"
REPORT_DIR="${ROOT}/_jobs/reports"
EVIDENCE_ROOT="${ROOT}/evidence"
RUNTIME_ROOT="${ROOT}/_runtime"
MIRROR_DIR="${RUNTIME_ROOT}/git_mirror/stellcodex.git"
SUMMARY_JSON="${REPORT_DIR}/stellcodex_git_sync_latest.json"
SUMMARY_MD="${REPORT_DIR}/stellcodex_git_sync_latest.md"
LOCK_WAIT_SECONDS="${STELLCODEX_GIT_SYNC_LOCK_WAIT_SECONDS:-0}"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="${EVIDENCE_ROOT}/git_sync_${TS}"

mkdir -p "${REPORT_DIR}" "${EVIDENCE_ROOT}" "${RUNTIME_ROOT}/git_mirror" "${RUN_DIR}"

if ! stellcodex_acquire_lock "heavy_ops" "${LOCK_WAIT_SECONDS}"; then
  echo "git sync skipped: heavy_ops lock busy" >&2
  exit 0
fi

if ! command -v git >/dev/null 2>&1; then
  echo "git is required" >&2
  exit 1
fi

if [[ ! -d "${REPO_DIR}/.git" ]]; then
  echo "repo not found: ${REPO_DIR}" >&2
  exit 1
fi

if ! command -v rclone >/dev/null 2>&1; then
  echo "rclone is required" >&2
  exit 1
fi

upload_if_present() {
  local src="$1"
  local dst="$2"
  local latest_name="$3"
  local summary_path="$4"
  if [[ -f "${src}" ]]; then
    "${ROOT}/scripts/drive_dedup_upload.sh" "${src}" "${dst}" "${latest_name}" >"${summary_path}"
  fi
}

BRANCH="$(git -C "${REPO_DIR}" branch --show-current || true)"
if [[ -z "${BRANCH}" ]]; then
  BRANCH="master"
fi
UPSTREAM_REF="$(git -C "${REPO_DIR}" rev-parse --abbrev-ref --symbolic-full-name "@{u}" 2>/dev/null || true)"
if [[ -z "${UPSTREAM_REF}" ]]; then
  UPSTREAM_REF="${REMOTE_NAME}/${BRANCH}"
fi

REMOTE_URL="$(git -C "${REPO_DIR}" remote get-url "${REMOTE_NAME}")"
LOCAL_HEAD="$(git -C "${REPO_DIR}" rev-parse HEAD)"
LAST_COMMIT="$(git -C "${REPO_DIR}" log -1 --format="%cI %H %s")"
STATUS_SHORT="$(git -C "${REPO_DIR}" status --short || true)"
TRACKED_CHANGES="$(git -C "${REPO_DIR}" status --porcelain --untracked-files=no | sed '/^$/d' | wc -l | tr -d ' ')"
UNTRACKED_CHANGES="$(git -C "${REPO_DIR}" status --porcelain | awk '/^\?\? / { c += 1 } END { print c + 0 }')"
WORKTREE_CLEAN="false"
if [[ -z "${STATUS_SHORT}" ]]; then
  WORKTREE_CLEAN="true"
fi

FETCH_STATUS="ok"
if ! git -C "${REPO_DIR}" fetch --prune "${REMOTE_NAME}" >"${RUN_DIR}/workspace_fetch.log" 2>&1; then
  FETCH_STATUS="failed"
fi

REMOTE_HEAD="$(git -C "${REPO_DIR}" rev-parse "${UPSTREAM_REF}" 2>/dev/null || true)"
AHEAD_COUNT=0
BEHIND_COUNT=0
if [[ -n "${REMOTE_HEAD}" ]]; then
  COUNTS="$(git -C "${REPO_DIR}" rev-list --left-right --count HEAD..."${UPSTREAM_REF}" 2>/dev/null || echo "0 0")"
  AHEAD_COUNT="$(awk '{print $1}' <<<"${COUNTS}")"
  BEHIND_COUNT="$(awk '{print $2}' <<<"${COUNTS}")"
fi

MIRROR_STATUS="updated"
if [[ ! -d "${MIRROR_DIR}" ]]; then
  if git clone --mirror "${REMOTE_URL}" "${MIRROR_DIR}" >"${RUN_DIR}/mirror_clone.log" 2>&1; then
    MIRROR_STATUS="cloned"
  else
    MIRROR_STATUS="clone_failed"
  fi
else
  git -C "${MIRROR_DIR}" remote set-url origin "${REMOTE_URL}" >/dev/null 2>&1 || true
  if git -C "${MIRROR_DIR}" fetch --prune --tags origin >"${RUN_DIR}/mirror_fetch.log" 2>&1; then
    MIRROR_STATUS="updated"
  else
    MIRROR_STATUS="fetch_failed"
  fi
fi

MIRROR_HEAD=""
if [[ -d "${MIRROR_DIR}" ]]; then
  MIRROR_HEAD="$(git -C "${MIRROR_DIR}" rev-parse "${UPSTREAM_REF}" 2>/dev/null || true)"
fi

WORKSPACE_APPLY_STATUS="fetch_only_by_policy"
if [[ "${WORKTREE_CLEAN}" != "true" ]]; then
  WORKSPACE_APPLY_STATUS="skipped_dirty_worktree"
elif [[ -n "${REMOTE_HEAD}" && "${LOCAL_HEAD}" == "${REMOTE_HEAD}" ]]; then
  WORKSPACE_APPLY_STATUS="already_at_remote_head"
fi

python3 - <<'PY' \
  "${SUMMARY_JSON}" \
  "${SUMMARY_MD}" \
  "${TS}" \
  "${REPO_DIR}" \
  "${REMOTE_NAME}" \
  "${REMOTE_URL}" \
  "${BRANCH}" \
  "${UPSTREAM_REF}" \
  "${LOCAL_HEAD}" \
  "${REMOTE_HEAD}" \
  "${MIRROR_HEAD}" \
  "${LAST_COMMIT}" \
  "${FETCH_STATUS}" \
  "${MIRROR_STATUS}" \
  "${WORKTREE_CLEAN}" \
  "${TRACKED_CHANGES}" \
  "${UNTRACKED_CHANGES}" \
  "${AHEAD_COUNT}" \
  "${BEHIND_COUNT}" \
  "${WORKSPACE_APPLY_STATUS}" \
  "${MIRROR_DIR}" \
  "${RUN_DIR}" \
  "${STATUS_SHORT}"
import json
import sys
from pathlib import Path

summary_json = Path(sys.argv[1])
summary_md = Path(sys.argv[2])
status_short = sys.argv[23]

payload = {
    "generated_at": sys.argv[3],
    "repo_dir": sys.argv[4],
    "remote_name": sys.argv[5],
    "remote_url": sys.argv[6],
    "branch": sys.argv[7],
    "upstream_ref": sys.argv[8],
    "local_head": sys.argv[9],
    "remote_head": sys.argv[10] or None,
    "mirror_head": sys.argv[11] or None,
    "last_commit": sys.argv[12],
    "fetch_status": sys.argv[13],
    "mirror_status": sys.argv[14],
    "worktree_clean": sys.argv[15] == "true",
    "tracked_changes": int(sys.argv[16]),
    "untracked_changes": int(sys.argv[17]),
    "ahead_count": int(sys.argv[18]),
    "behind_count": int(sys.argv[19]),
    "workspace_apply_status": sys.argv[20],
    "mirror_dir": sys.argv[21],
    "run_dir": sys.argv[22],
    "status_excerpt": status_short.splitlines()[:80],
    "policy": {
        "mode": "fetch_only",
        "reason": "Server runtime is disposable; the guard verifies and mirrors GitHub state without mutating a dirty live workspace.",
    },
}
summary_json.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
lines = [
    "# STELLCODEX GitHub Sync Guard",
    "",
    f"- generated_at: {payload['generated_at']}",
    f"- repo_dir: {payload['repo_dir']}",
    f"- remote_url: {payload['remote_url']}",
    f"- branch: {payload['branch']}",
    f"- upstream_ref: {payload['upstream_ref']}",
    f"- local_head: {payload['local_head']}",
    f"- remote_head: {payload['remote_head'] or 'unavailable'}",
    f"- mirror_head: {payload['mirror_head'] or 'unavailable'}",
    f"- fetch_status: {payload['fetch_status']}",
    f"- mirror_status: {payload['mirror_status']}",
    f"- worktree_clean: {payload['worktree_clean']}",
    f"- tracked_changes: {payload['tracked_changes']}",
    f"- untracked_changes: {payload['untracked_changes']}",
    f"- ahead_count: {payload['ahead_count']}",
    f"- behind_count: {payload['behind_count']}",
    f"- workspace_apply_status: {payload['workspace_apply_status']}",
    f"- policy: {payload['policy']['mode']} ({payload['policy']['reason']})",
    "",
    "## Status Excerpt",
]
if payload["status_excerpt"]:
    lines.extend(f"- {item}" for item in payload["status_excerpt"])
else:
    lines.append("- clean")
summary_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

upload_if_present \
  "${SUMMARY_JSON}" \
  "${REMOTE_BASE}/12_reports/github_sync" \
  "stellcodex_git_sync_latest.json" \
  "${RUN_DIR}/git_sync_json_upload.json"

upload_if_present \
  "${SUMMARY_MD}" \
  "${REMOTE_BASE}/12_reports/github_sync" \
  "stellcodex_git_sync_latest.md" \
  "${RUN_DIR}/git_sync_md_upload.json"
