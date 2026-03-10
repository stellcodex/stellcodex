#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
mkdir -p "${LOG_DIR}"

export HF_HOME=/root/workspace/_models
export TRANSFORMERS_CACHE=/root/workspace/_models
export STELL_AI_VECTOR_STORE=/root/workspace/_vector_store

"${ROOT_DIR}/.venv/bin/python" "${ROOT_DIR}/tests/embedding_smoke.py" > "${LOG_DIR}/embedding_smoke.json"
"${ROOT_DIR}/.venv/bin/python" "${ROOT_DIR}/tests/chroma_smoke.py" > "${LOG_DIR}/chroma_smoke.json"
"${ROOT_DIR}/.venv/bin/python" "${ROOT_DIR}/tests/bm25_smoke.py" > "${LOG_DIR}/bm25_smoke.json"
"${ROOT_DIR}/.venv/bin/python" "${ROOT_DIR}/tests/event_smoke.py" > "${LOG_DIR}/event_smoke.json"
