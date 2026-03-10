#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
mkdir -p "${ROOT_DIR}/tests" "${ROOT_DIR}/scripts" "${ROOT_DIR}/examples" "${LOG_DIR}" /root/workspace/_models /root/workspace/_vector_store

PYTHON_BIN="${PYTHON_BIN:-}"
if [[ -z "${PYTHON_BIN}" ]]; then
  if command -v python3.9 >/dev/null 2>&1; then
    PYTHON_BIN="python3.9"
  else
    PYTHON_BIN="python3"
  fi
fi

if [[ ! -d "${ROOT_DIR}/.venv" ]]; then
  "${PYTHON_BIN}" -m venv "${ROOT_DIR}/.venv"
fi

"${ROOT_DIR}/.venv/bin/python" -m pip install --upgrade pip setuptools wheel > "${LOG_DIR}/venv_bootstrap.log" 2>&1
echo "${ROOT_DIR}/.venv"
