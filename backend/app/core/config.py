from __future__ import annotations

from functools import lru_cache
from typing import Optional, List

from pydantic import AnyUrl, Field, AliasChoices, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # REQUIRED
    database_url: AnyUrl = Field(..., validation_alias="DATABASE_URL")
    jwt_secret: str | None = Field(
        default=None,
        min_length=32,
        validation_alias=AliasChoices("JWT_SECRET", "SECRET_KEY", "APP_SECRET", "SIGNING_KEY"),
    )
    jwt_alg: str = Field(default="HS256", validation_alias="JWT_ALG")

    # Token settings
    access_token_minutes: int = Field(default=30, validation_alias="ACCESS_TOKEN_MINUTES")
    refresh_token_days: int = Field(default=14, validation_alias="REFRESH_TOKEN_DAYS")


    # Admin bootstrap
    bootstrap_admin_email: str | None = Field(default=None, validation_alias="BOOTSTRAP_ADMIN_EMAIL")
    bootstrap_admin_token: str | None = Field(default=None, validation_alias="BOOTSTRAP_ADMIN_TOKEN")

    # Auth/session
    site_url: str | None = Field(default=None, validation_alias=AliasChoices("SITE_URL", "APP_URL"))
    auth_session_cookie_name: str = Field(default="stellcodex_session", validation_alias="AUTH_SESSION_COOKIE_NAME")
    auth_google_state_cookie_name: str = Field(default="stellcodex_google_state", validation_alias="AUTH_GOOGLE_STATE_COOKIE_NAME")
    auth_session_ttl_minutes: int = Field(default=7 * 24 * 60, validation_alias="AUTH_SESSION_TTL_MINUTES")
    auth_google_state_ttl_minutes: int = Field(default=15, validation_alias="AUTH_GOOGLE_STATE_TTL_MINUTES")
    google_client_id: str | None = Field(default=None, validation_alias=AliasChoices("GOOGLE_CLIENT_ID", "AUTH_GOOGLE_CLIENT_ID"))
    google_client_secret: str | None = Field(default=None, validation_alias=AliasChoices("GOOGLE_CLIENT_SECRET", "AUTH_GOOGLE_CLIENT_SECRET"))
    google_redirect_uri: str | None = Field(default=None, validation_alias=AliasChoices("GOOGLE_REDIRECT_URI", "AUTH_GOOGLE_REDIRECT_URI"))
    google_admin_whitelist_raw: str = Field(default="", validation_alias=AliasChoices("GOOGLE_ADMIN_WHITELIST", "AUTH_GOOGLE_ADMIN_WHITELIST"))
    auth_seed_admin_email: str | None = Field(default=None, validation_alias="AUTH_SEED_ADMIN_EMAIL")
    auth_seed_admin_password: str | None = Field(default=None, validation_alias="AUTH_SEED_ADMIN_PASSWORD")
    auth_seed_admin_full_name: str | None = Field(default="STELLCODEX Admin", validation_alias="AUTH_SEED_ADMIN_FULL_NAME")
    auth_seed_member_email: str | None = Field(default=None, validation_alias="AUTH_SEED_MEMBER_EMAIL")
    auth_seed_member_password: str | None = Field(default=None, validation_alias="AUTH_SEED_MEMBER_PASSWORD")
    auth_seed_member_full_name: str | None = Field(default="STELLCODEX Member", validation_alias="AUTH_SEED_MEMBER_FULL_NAME")

    # OPTIONAL infra
    redis_url: Optional[AnyUrl] = Field(default=None, validation_alias="REDIS_URL")
    rabbitmq_url: Optional[AnyUrl] = Field(default=None, validation_alias="RABBITMQ_URL")

    celery_broker_url: Optional[AnyUrl] = Field(default=None, validation_alias="CELERY_BROKER_URL")
    celery_result_backend: Optional[AnyUrl] = Field(default=None, validation_alias="CELERY_RESULT_BACKEND")

    # Feature flags
    feature_files: bool = Field(default=True, validation_alias="FEATURE_FILES")

    # Upload limits
    max_upload_bytes: int = Field(default=200 * 1024 * 1024, validation_alias="MAX_UPLOAD_BYTES")
    allowed_content_types_raw: str = Field(default="", validation_alias="ALLOWED_CONTENT_TYPES")

    # Conversion binaries
    freecad_bin: str = Field(default="/usr/local/bin/freecad", validation_alias="FREECAD_BIN")
    blender_bin: str = Field(default="/usr/local/bin/blender", validation_alias="BLENDER_BIN")
    conversion_timeout_seconds: int = Field(default=600, validation_alias="CONVERSION_TIMEOUT_SECONDS")
    blender_timeout_seconds: int = Field(default=120, validation_alias="BLENDER_TIMEOUT_SECONDS")

    @property
    def allowed_content_types(self) -> List[str]:
        raw = (self.allowed_content_types_raw or "").strip()
        if not raw:
            return []
        return [x.strip() for x in raw.split(",") if x.strip()]

    @property
    def google_admin_whitelist(self) -> List[str]:
        raw = (self.google_admin_whitelist_raw or "").strip()
        if not raw:
            return []
        return [x.strip().lower() for x in raw.split(",") if x.strip()]

    # S3 / MinIO (optional)
    s3_endpoint_url: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("STELLCODEX_S3_ENDPOINT_URL", "MINIO_ENDPOINT"),
    )
    s3_region: Optional[str] = Field(default=None, validation_alias="STELLCODEX_S3_REGION")
    s3_bucket: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("STELLCODEX_S3_BUCKET", "MINIO_BUCKET"),
    )
    s3_access_key_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("STELLCODEX_S3_ACCESS_KEY_ID", "MINIO_ACCESS_KEY"),
    )
    s3_secret_access_key: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("STELLCODEX_S3_SECRET_ACCESS_KEY", "MINIO_SECRET_KEY"),
    )
    s3_use_ssl: bool = Field(default=False, validation_alias="STELLCODEX_S3_USE_SSL")
    s3_verify_tls: bool = Field(default=True, validation_alias="STELLCODEX_S3_VERIFY_TLS")
    s3_force_path_style: bool = Field(default=True, validation_alias="STELLCODEX_S3_FORCE_PATH_STYLE")
    public_s3_base_url: Optional[AnyUrl] = Field(
        default=None,
        validation_alias=AliasChoices("PUBLIC_S3_BASE_URL", "STORAGE_PUBLIC_BASE_URL"),
    )

    # Internal service authorities
    stell_ai_base_url: str = Field(default="http://stellai:7020", validation_alias="STELL_AI_BASE_URL")
    orchestra_base_url: str = Field(default="http://orchestra:7010", validation_alias="ORCHESTRA_BASE_URL")

    @property
    def s3_enabled(self) -> bool:
        return all([self.s3_endpoint_url, self.s3_bucket, self.s3_access_key_id, self.s3_secret_access_key])

    @model_validator(mode="after")
    def _ensure_jwt_secret(self):
        if not self.jwt_secret:
            raise ValueError("JWT secret env missing: set JWT_SECRET or SECRET_KEY")
        return self

    # ---- Legacy aliases (unused) ----
    @property
    def DATABASE_URL(self):
        return str(self.database_url)

    @property
    def JWT_SECRET(self):
        return self.jwt_secret

    @property
    def JWT_ALG(self):
        return self.jwt_alg

    @property
    def ACCESS_TOKEN_MINUTES(self):
        return self.access_token_minutes

    @property
    def REFRESH_TOKEN_DAYS(self):
        return self.refresh_token_days

    @property
    def REDIS_URL(self):
        return str(self.redis_url) if self.redis_url else None

    @property
    def RABBITMQ_URL(self):
        return str(self.rabbitmq_url) if self.rabbitmq_url else None

    @property
    def celery_broker(self):
        # prefer explicit CELERY_BROKER_URL; fallback to rabbitmq
        return str(self.celery_broker_url) if self.celery_broker_url else self.RABBITMQ_URL

    @property
    def celery_result(self):
        # prefer explicit CELERY_RESULT_BACKEND; fallback to redis
        return str(self.celery_result_backend) if self.celery_result_backend else self.REDIS_URL


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
