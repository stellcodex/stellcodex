#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
mkdir -p "${LOG_DIR}"

export HF_HOME=/root/workspace/_models
export TRANSFORMERS_CACHE=/root/workspace/_models
export STELL_AI_VECTOR_STORE=/root/workspace/_vector_store

"${ROOT_DIR}/.venv/bin/python" "${ROOT_DIR}/tests/import_smoke.py" > "${LOG_DIR}/import_smoke_run1.json"
"${ROOT_DIR}/.venv/bin/python" "${ROOT_DIR}/tests/import_smoke.py" > "${LOG_DIR}/import_smoke_run2.json"
