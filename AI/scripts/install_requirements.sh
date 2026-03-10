#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
LOG_DIR="${ROOT_DIR}/logs"
mkdir -p "${LOG_DIR}" /root/workspace/_models /root/workspace/_vector_store

export HF_HOME=/root/workspace/_models
export TRANSFORMERS_CACHE=/root/workspace/_models
export STELL_AI_VECTOR_STORE=/root/workspace/_vector_store

"${VENV_DIR}/bin/python" -m pip install -r "${ROOT_DIR}/requirements.in" > "${LOG_DIR}/pip_install.log" 2>&1
"${VENV_DIR}/bin/python" -m pip freeze > "${ROOT_DIR}/requirements.lock"
"${VENV_DIR}/bin/python" -m pip freeze > "${LOG_DIR}/pip_freeze.log"
"${VENV_DIR}/bin/python" -m pip check > "${LOG_DIR}/pip_check.log" 2>&1
