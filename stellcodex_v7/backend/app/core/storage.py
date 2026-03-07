from __future__ import annotations

import logging

import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import BotoCoreError, ClientError, EndpointConnectionError

from app.core.config import Settings

log = logging.getLogger("stellcodex.storage")


def _build_s3_client(settings: Settings, endpoint_url: str | None, use_ssl: bool):
    boto_cfg = BotoConfig(
        retries={"max_attempts": 2, "mode": "standard"},
        connect_timeout=2,
        read_timeout=4,
        s3={"addressing_style": "path" if settings.s3_force_path_style else "virtual"},
        signature_version="s3v4",
    )
    session = boto3.session.Session()
    return session.client(
        "s3",
        endpoint_url=endpoint_url,
        region_name=settings.s3_region,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
        use_ssl=use_ssl,
        verify=settings.s3_verify_tls,
        config=boto_cfg,
    )


def get_s3_client(settings: Settings) -> boto3.client:
    if not settings.s3_enabled:
        raise RuntimeError("S3 not configured")
    return _build_s3_client(settings, settings.s3_endpoint_url, settings.s3_use_ssl)


def get_s3_presign_client(settings: Settings) -> boto3.client:
    if not settings.s3_enabled:
        raise RuntimeError("S3 not configured")

    endpoint_url = settings.public_s3_base_url or settings.s3_endpoint_url
    if settings.public_s3_base_url:
        endpoint_url = str(settings.public_s3_base_url).rstrip("/")
        use_ssl = endpoint_url.startswith("https://")
    else:
        use_ssl = settings.s3_use_ssl
    return _build_s3_client(settings, endpoint_url, use_ssl)


def ensure_bucket_exists(settings: Settings) -> bool:
    if not settings.s3_enabled:
        log.warning("S3 disabled: missing STELLCODEX_S3_* configuration. Bucket check skipped.")
        return False

    s3 = _build_s3_client(settings, settings.s3_endpoint_url, settings.s3_use_ssl)
    bucket = settings.s3_bucket

    try:
        s3.head_bucket(Bucket=bucket)
        log.info("S3 bucket is present: %s", bucket)
        return True
    except ClientError as e:
        code = str(e.response.get("Error", {}).get("Code", ""))
        if code in {"404", "NoSuchBucket", "NotFound"}:
            try:
                if settings.s3_region:
                    s3.create_bucket(
                        Bucket=bucket,
                        CreateBucketConfiguration={"LocationConstraint": settings.s3_region},
                    )
                else:
                    s3.create_bucket(Bucket=bucket)
                log.warning("S3 bucket created: %s", bucket)
                return True
            except (ClientError, BotoCoreError) as ce:
                log.warning("S3 bucket create failed (fail-soft): %s", ce, exc_info=True)
                return False

        log.warning("S3 head_bucket failed (fail-soft): %s", e, exc_info=True)
        return False
    except (EndpointConnectionError, BotoCoreError) as e:
        log.warning("S3 unavailable (fail-soft): %s", e, exc_info=True)
        return False
