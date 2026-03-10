#!/usr/bin/env bash
set -euo pipefail

ROOT="/root/workspace"
REPORT_DIR="${ROOT}/_jobs/reports"
SUMMARY_JSON="${REPORT_DIR}/stellcodex_cleanup_latest.json"
SUMMARY_MD="${REPORT_DIR}/stellcodex_cleanup_latest.md"
MAX_AGE_MINUTES="${MAX_AGE_MINUTES:-1440}"

mkdir -p "${REPORT_DIR}"

DIRS=(
  "/tmp/stellcodex_output/evidence"
  "/tmp/stellcodex_output/tmp"
  "${ROOT}/evidence"
  "${ROOT}/_jobs/output"
  "${ROOT}/cache"
)

declare -a REMOVED_ITEMS=()
declare -a DIR_SUMMARIES=()

for dir in "${DIRS[@]}"; do
  if [[ ! -d "${dir}" ]]; then
    DIR_SUMMARIES+=("${dir}|missing|0|0")
    continue
  fi

  BEFORE_COUNT="$(find "${dir}" -mindepth 1 -maxdepth 1 | wc -l | awk '{print $1}')"
  REMOVED_COUNT=0
  while IFS= read -r -d '' item; do
    REMOVED_ITEMS+=("${item}")
    rm -rf "${item}"
    REMOVED_COUNT=$((REMOVED_COUNT + 1))
  done < <(find "${dir}" -mindepth 1 -maxdepth 1 -mmin +"${MAX_AGE_MINUTES}" -print0)
  AFTER_COUNT="$(find "${dir}" -mindepth 1 -maxdepth 1 | wc -l | awk '{print $1}')"
  DIR_SUMMARIES+=("${dir}|ok|${BEFORE_COUNT}|${AFTER_COUNT}")
done

python3 - <<'PY' "${SUMMARY_JSON}" "${SUMMARY_MD}" "${MAX_AGE_MINUTES}" "${#REMOVED_ITEMS[@]}" "${#DIR_SUMMARIES[@]}" "${DIR_SUMMARIES[@]}" -- "${REMOVED_ITEMS[@]}"
import json
import sys
from pathlib import Path

summary_json = Path(sys.argv[1])
summary_md = Path(sys.argv[2])
max_age_minutes = int(sys.argv[3])
removed_total = int(sys.argv[4])
dir_summary_count = int(sys.argv[5])
dir_summaries = sys.argv[6 : 6 + dir_summary_count]
removed_items = sys.argv[7 + dir_summary_count :]
if removed_items and removed_items[0] == "--":
    removed_items = removed_items[1:]

dirs = []
for row in dir_summaries:
    path, status, before, after = row.split("|", 3)
    dirs.append(
        {
            "path": path,
            "status": status,
            "before_count": int(before),
            "after_count": int(after),
            "removed_count": int(before) - int(after) if status == "ok" else 0,
        }
    )

payload = {
    "max_age_minutes": max_age_minutes,
    "removed_total": removed_total,
    "directories": dirs,
    "removed_items": removed_items,
}
summary_json.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

lines = [
    "# STELLCODEX Artifact Cleanup",
    "",
    f"- max_age_minutes: {max_age_minutes}",
    f"- removed_total: {removed_total}",
    "",
    "## Directory Results",
]
for item in dirs:
    lines.append(
        f"- {item['path']}: status={item['status']} before={item['before_count']} after={item['after_count']} removed={item['removed_count']}"
    )
lines.append("")
lines.append("## Removed Items")
if removed_items:
    lines.extend(f"- {item}" for item in removed_items)
else:
    lines.append("- none")
summary_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY
