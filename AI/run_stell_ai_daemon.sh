#!/usr/bin/env bash
set -euo pipefail

source /root/workspace/AI/.venv/bin/activate
export PYTHONPATH=/root/workspace/AI
exec python -m stell_ai.daemon
