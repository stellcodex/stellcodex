#!/usr/bin/env bash
set -euo pipefail

PY_BIN="${1:-/root/workspace/AI/.venv/bin/python}"
if [[ ! -x "$PY_BIN" ]]; then
  echo "python_not_found: $PY_BIN" >&2
  exit 1
fi

PIP_BIN="$(dirname "$PY_BIN")/pip"
if [[ ! -x "$PIP_BIN" ]]; then
  echo "pip_not_found: $PIP_BIN" >&2
  exit 1
fi

# Python 3.8-compatible RAG stack baseline.
# Keep langchain family pinned to avoid resolver backtracking and unintended downgrades.
"$PIP_BIN" install \
  litellm \
  "langchain==0.2.17" \
  "langchain-core==0.2.43" \
  "langchain-community==0.2.19" \
  "langchain-text-splitters==0.2.4" \
  "llama-index==0.10.68" \
  "chromadb==0.4.22" \
  "qdrant-client==1.12.1" \
  "sentence-transformers==3.2.1" \
  "rank-bm25==0.2.2" \
  opentelemetry-api \
  pysqlite3-binary

# For Python 3.8, the available langgraph build is yanked and has outdated constraints.
# Install without dependency resolution so pinned langchain packages remain intact.
"$PIP_BIN" install --no-deps "langgraph==0.0.8"

SITE_PACKAGES="$("$PY_BIN" -c 'import site; print(site.getsitepackages()[0])')"

# Force sqlite3 imports to use pysqlite3 for chromadb compatibility.
cat > "${SITE_PACKAGES}/zz_sqlite_patch.pth" <<'PTH'
import sys,pysqlite3;sys.modules["sqlite3"]=pysqlite3
PTH

echo "rag_runtime_bootstrap=ok"
echo "python=${PY_BIN}"
echo "site_packages=${SITE_PACKAGES}"
