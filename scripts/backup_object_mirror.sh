#!/usr/bin/env bash
set -euo pipefail

# Uses MinIO client if available, otherwise falls back to rclone or aws s3 sync for local path targets.
# Configure:
#   SRC_ALIAS, DST_ALIAS or DST_PATH, BUCKET
#   or SRC_ENDPOINT_URL + AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY for rclone/aws fallback
SRC_ALIAS="${SRC_ALIAS:-minio-src}"
DST_ALIAS="${DST_ALIAS:-minio-dst}"
DST_PATH="${DST_PATH:-./backups/object_mirror}"
BUCKET="${BUCKET:-stellcodex}"
SRC_ENDPOINT_URL="${SRC_ENDPOINT_URL:-}"
AWS_REGION="${AWS_REGION:-us-east-1}"
MINIO_CONTAINER="${MINIO_CONTAINER:-stellcodex-minio}"

MC_BIN=""
if command -v mcli >/dev/null 2>&1; then
  MC_BIN="$(command -v mcli)"
elif command -v mc >/dev/null 2>&1 && mc --help 2>&1 | grep -qi "MinIO Client"; then
  MC_BIN="$(command -v mc)"
fi

if [ -n "$MC_BIN" ]; then
  if [ -n "$DST_PATH" ]; then
    mkdir -p "$DST_PATH"
    TARGET="${DST_PATH%/}/${BUCKET}"
    echo "Mirroring bucket $BUCKET from $SRC_ALIAS to local path $TARGET"
    "$MC_BIN" mirror --overwrite "$SRC_ALIAS/$BUCKET" "$TARGET"
  else
    echo "Mirroring bucket $BUCKET from $SRC_ALIAS to $DST_ALIAS"
    "$MC_BIN" mirror --overwrite "$SRC_ALIAS/$BUCKET" "$DST_ALIAS/$BUCKET"
  fi
elif [ -n "$DST_PATH" ] && command -v rclone >/dev/null 2>&1 && [ -n "$SRC_ENDPOINT_URL" ]; then
  mkdir -p "${DST_PATH%/}/${BUCKET}"
  echo "Mirroring bucket $BUCKET from $SRC_ENDPOINT_URL to local path ${DST_PATH%/}/${BUCKET} via rclone"
  RCLONE_ENDPOINT="${SRC_ENDPOINT_URL#http://}"
  RCLONE_ENDPOINT="${RCLONE_ENDPOINT#https://}"
  rclone sync \
    ":s3,provider=Minio,env_auth=false,access_key_id=${AWS_ACCESS_KEY_ID:-},secret_access_key=${AWS_SECRET_ACCESS_KEY:-},endpoint=${RCLONE_ENDPOINT},use_http=true,region=${AWS_REGION}:${BUCKET}" \
    "${DST_PATH%/}/${BUCKET}"
elif [ -n "$DST_PATH" ] && command -v aws >/dev/null 2>&1 && [ -n "$SRC_ENDPOINT_URL" ]; then
  mkdir -p "${DST_PATH%/}/${BUCKET}"
  echo "Mirroring bucket $BUCKET from $SRC_ENDPOINT_URL to local path ${DST_PATH%/}/${BUCKET} via aws s3 sync"
  aws --endpoint-url "$SRC_ENDPOINT_URL" s3 sync "s3://${BUCKET}" "${DST_PATH%/}/${BUCKET}" --region "$AWS_REGION"
elif [ -n "$DST_PATH" ] && command -v docker >/dev/null 2>&1; then
  mkdir -p "${DST_PATH%/}/${BUCKET}"
  echo "Mirroring bucket $BUCKET from container ${MINIO_CONTAINER}:/data/${BUCKET} to local path ${DST_PATH%/}/${BUCKET} via docker cp"
  rm -rf "${DST_PATH%/}/${BUCKET}"
  mkdir -p "${DST_PATH%/}/${BUCKET}"
  docker cp "${MINIO_CONTAINER}:/data/${BUCKET}/." "${DST_PATH%/}/${BUCKET}/"
else
  echo "ERROR: no usable object mirror client found (need mcli/MinIO mc, rclone/aws + SRC_ENDPOINT_URL, or docker cp fallback for DST_PATH mode)" >&2
  exit 2
fi

echo "PASS: object mirror"
