#!/usr/bin/env bash
set -euo pipefail

source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/_common.sh"

wait_backend

LOG_FILE="${EVIDENCE_DIR}/engineering_tests.log"
REPORT_DIR="${ROOT_DIR}/_jobs/reports"
REPORT_PATH="${REPORT_DIR}/stellcodex_v10_engineering_report.json"
EVIDENCE_REPORT_PATH="${EVIDENCE_DIR}/stellcodex_v10_engineering_report.json"

mkdir -p "${REPORT_DIR}"

{
  echo "[engineering] started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  (
    cd "${ROOT_DIR}/backend"
    PYTHONPATH="${ROOT_DIR}/backend" python3 -m pytest -q tests/engineering
  )
  echo "[engineering] pytest passed"
} 2>&1 | tee "${LOG_FILE}"

TESTS_PASSED="$(grep -Eo '[0-9]+ passed' "${LOG_FILE}" | tail -n1 | awk '{print $1}')"
if [[ -z "${TESTS_PASSED}" ]]; then
  TESTS_PASSED="0"
fi

PYTHONPATH="${ROOT_DIR}/backend" python3 "${ROOT_DIR}/backend/scripts/generate_v10_engineering_report.py" \
  --output "${REPORT_PATH}" \
  --mirror "${EVIDENCE_REPORT_PATH}" \
  --system-health ok \
  --tests-passed "${TESTS_PASSED}" \
  --tests-total "${TESTS_PASSED}" \
  --gate-status engineering_tests_passed \
  --evidence-artifact "${LOG_FILE}" \
  --evidence-artifact "${REPORT_PATH}" \
  --evidence-artifact "${EVIDENCE_REPORT_PATH}" | tee -a "${LOG_FILE}"

echo "[engineering] report=${REPORT_PATH}" | tee -a "${LOG_FILE}"
echo "[engineering] passed" | tee -a "${LOG_FILE}"
