from __future__ import annotations

import os
import time
import logging
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

log = logging.getLogger("uvicorn.error")

def _env(name: str, default: str | None = None) -> str | None:
    v = os.getenv(name, default)
    if v is None:
        return None
    v = v.strip()
    return v if v else None

def get_s3_client():
    endpoint = _env("STELLCODEX_S3_ENDPOINT_URL") or _env("STELLCODEX_S3_ENDPOINT")
    access_key = _env("STELLCODEX_S3_ACCESS_KEY_ID") or _env("STELLCODEX_S3_ACCESS_KEY")
    secret_key = _env("STELLCODEX_S3_SECRET_ACCESS_KEY") or _env("STELLCODEX_S3_SECRET_KEY")
    region = _env("STELLCODEX_S3_REGION", "us-east-1")

    if not endpoint or not access_key or not secret_key:
        raise RuntimeError(
            "S3 env eksik. Gerekli: STELLCODEX_S3_ENDPOINT_URL/STELLCODEX_S3_ENDPOINT, STELLCODEX_S3_ACCESS_KEY_ID/STELLCODEX_S3_ACCESS_KEY, STELLCODEX_S3_SECRET_ACCESS_KEY/STELLCODEX_S3_SECRET_KEY"
        )

    # MinIO için: signature v4 + path-style adresleme
    cfg = Config(signature_version="s3v4", s3={"addressing_style": "path"})
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
        config=cfg,
    )

def ensure_bucket_exists(max_wait_seconds: int = 30):
    log.info("BOOTSTRAP ensure_bucket_exists() called")
    bucket = _env("STELLCODEX_S3_BUCKET")
    if not bucket:
        raise RuntimeError("Bucket env eksik: STELLCODEX_S3_BUCKET")

    s3 = get_s3_client()

    # MinIO bazen container yeni kalkınca çok kısa süre hazır olmuyor -> kısa retry
    deadline = time.time() + max_wait_seconds
    last_err = None

    while time.time() < deadline:
        try:
            # varsa sorun yok
            s3.head_bucket(Bucket=bucket)
            log.info("MinIO bucket OK: %s", bucket)
            return

        except ClientError as e:
            code = str(e.response.get("Error", {}).get("Code", ""))
            # bucket yoksa oluştur
            if code in ("404", "NoSuchBucket", "NotFound"):
                try:
                    log.info("BOOTSTRAP creating bucket...")
                    s3.create_bucket(Bucket=bucket)
                    log.info("MinIO bucket created: %s", bucket)
                    return
                except ClientError as ce:
                    last_err = ce
                    log.warning("Bucket create failed, retrying... err=%s", ce)
                    time.sleep(2)
                    continue

            # minio hazır değil / bağlantı vb -> retry
            last_err = e
            log.warning("Bucket head failed, retrying... err=%s", e)
            time.sleep(2)
            continue

        except Exception as e:
            last_err = e
            log.warning("MinIO check error, retrying... err=%s", e)
            time.sleep(2)
            continue

    raise RuntimeError(f"MinIO bucket init failed. bucket={bucket} last_err={last_err}")

