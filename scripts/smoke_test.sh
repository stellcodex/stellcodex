#!/usr/bin/env bash
set -euo pipefail

exec /root/workspace/stellcodex_v7/infrastructure/deploy/scripts/smoke_test.sh "$@"
