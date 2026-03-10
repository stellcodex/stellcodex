#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/root/workspace}"
OUT_DIR="${2:-$ROOT/_runs/repo_split_$(date -u +%Y%m%dT%H%M%SZ)}"
mkdir -p "$OUT_DIR"

# Export snapshots for immediate independent-repo bootstrap.
tar -czf "$OUT_DIR/stell-ai.tar.gz" -C "$ROOT" stell-ai AI/stell_ai
tar -czf "$OUT_DIR/orchestra.tar.gz" -C "$ROOT" orchestra ops/orchestra
tar -czf "$OUT_DIR/stellcodex.tar.gz" -C "$ROOT" stellcodex stellcodex_v7/backend
tar -czf "$OUT_DIR/infra.tar.gz" -C "$ROOT" infra stellcodex_v7/infrastructure

cat > "$OUT_DIR/README.txt" <<'TXT'
Repository split bundle created.

Artifacts:
- stell-ai.tar.gz
- orchestra.tar.gz
- stellcodex.tar.gz
- infra.tar.gz

Usage:
1) Extract each archive into a clean directory.
2) Initialize each as an independent git repository.
3) Add remote and push.
4) Configure per-repo CI and branch protections.
TXT

echo "bundle_dir=$OUT_DIR"
echo "PASS repo-split-bundle"
