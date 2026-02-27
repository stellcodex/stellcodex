#!/usr/bin/env bash
set -euo pipefail

# Uses mc (MinIO client) if available. Otherwise, this is a template.
# Configure:
#   SRC_ALIAS, DST_ALIAS, BUCKET
SRC_ALIAS="${SRC_ALIAS:-minio-src}"
DST_ALIAS="${DST_ALIAS:-minio-dst}"
BUCKET="${BUCKET:-stellcodex}"

command -v mc >/dev/null 2>&1 || { echo "ERROR: mc not installed (minio client)"; exit 2; }

echo "Mirroring bucket $BUCKET from $SRC_ALIAS to $DST_ALIAS"
mc mirror --overwrite "$SRC_ALIAS/$BUCKET" "$DST_ALIAS/$BUCKET"
echo "PASS: object mirror"
