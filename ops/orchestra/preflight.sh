#!/usr/bin/env bash
set -euo pipefail

JOBS_ROOT="${1:-/root/workspace/_jobs}"
LOG_DIR="${JOBS_ROOT}/logs"
REPORT_PATH="${LOG_DIR}/PREFLIGHT_REPORT.md"
SNAPSHOT_PATH="${LOG_DIR}/PREFLIGHT_SNAPSHOT.json"
BASE_URL="${BASE_URL:-http://localhost:7010}"

mkdir -p "${LOG_DIR}"

run_capture() {
  local name="$1"
  shift
  if "$@" >"${LOG_DIR}/preflight_${name}.txt" 2>&1; then
    return 0
  fi
  return 1
}

run_capture "uname" uname -a || true
run_capture "lscpu" lscpu || true
run_capture "free" free -h || true
run_capture "df" df -h || true
run_capture "uptime" uptime || true
run_capture "docker_info" docker info || true
run_capture "docker_ps" docker ps || true
run_capture "dns" getent hosts example.com || true
run_capture "curl_example" curl -I https://example.com || true
run_capture "git_status_root" git -C /root/workspace status --short --branch || true
run_capture "git_status_orchestra" git -C /root/workspace/ops/orchestra status --short --branch || true
run_capture "orchestra_state" curl -sS "${BASE_URL}/state" || true

workspace_ok="false"
orchestra_ok="false"
[[ -d /root/workspace ]] && workspace_ok="true"
[[ -d /root/workspace/ops/orchestra ]] && orchestra_ok="true"

{
  echo "# PREFLIGHT REPORT"
  echo
  echo "Generated At: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo
  echo "## Workspace Checks"
  echo "- /root/workspace exists: ${workspace_ok}"
  echo "- /root/workspace/ops/orchestra exists: ${orchestra_ok}"
  echo

  for name in uname lscpu free df uptime docker_info docker_ps dns curl_example git_status_root git_status_orchestra orchestra_state; do
    file="${LOG_DIR}/preflight_${name}.txt"
    [[ -f "${file}" ]] || continue
    echo "## ${name}"
    echo '```'
    sed -n '1,120p' "${file}"
    echo '```'
    echo
  done
} >"${REPORT_PATH}"

python3 - <<'PY' "${LOG_DIR}" "${SNAPSHOT_PATH}" "${workspace_ok}" "${orchestra_ok}"
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

log_dir = Path(sys.argv[1])
snapshot_path = Path(sys.argv[2])
workspace_ok = sys.argv[3] == "true"
orchestra_ok = sys.argv[4] == "true"

def read(name: str) -> str:
    path = log_dir / f"preflight_{name}.txt"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="ignore").strip()

payload = {
    "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "workspace_exists": workspace_ok,
    "orchestra_exists": orchestra_ok,
    "system": {
        "uname": read("uname"),
        "lscpu": read("lscpu"),
        "free_h": read("free"),
        "df_h": read("df"),
        "uptime": read("uptime"),
    },
    "docker": {
        "info": read("docker_info"),
        "ps": read("docker_ps"),
    },
    "network": {
        "dns": read("dns"),
        "curl_example": read("curl_example"),
    },
    "workspace": {
        "git_status_root": read("git_status_root"),
        "git_status_orchestra": read("git_status_orchestra"),
    },
    "service": {
        "orchestra_state": read("orchestra_state"),
    },
}

snapshot_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
PY

echo "PREFLIGHT_READY ${REPORT_PATH} ${SNAPSHOT_PATH}"
