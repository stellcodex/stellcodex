from fastapi import FastAPI
from sqlalchemy import text

from app.db import Base, engine
from app.db.session import SessionLocal
from app.models.file import UploadFile
from app.core.format_registry import get_rule_for_filename
from app.services.orchestrator_engine import seed_default_rule_configs
from app.core.config import settings
from app.core.storage import ensure_bucket_exists


def _compute_folder_key_for_row(row: UploadFile) -> str:
    meta = row.meta if isinstance(row.meta, dict) else {}
    project_id = str(meta.get("project_id") or "default")
    rule = get_rule_for_filename(row.original_filename or "")
    kind = (meta.get("kind") if isinstance(meta.get("kind"), str) else None) or (rule.kind if rule else "3d")
    mode = (meta.get("mode") if isinstance(meta.get("mode"), str) else None) or (rule.mode if rule else "brep")
    return f"project/{project_id}/{kind}/{mode}"


def _ensure_uploaded_files_schema() -> None:
    # create_all does not add new columns on existing tables.
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS folder_key TEXT"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_uploaded_files_folder_key ON uploaded_files (folder_key)"))
        conn.execute(text("ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS decision_json JSONB"))
        conn.execute(text("UPDATE uploaded_files SET decision_json = '{}'::jsonb WHERE decision_json IS NULL"))
        conn.execute(text("ALTER TABLE uploaded_files ALTER COLUMN decision_json SET NOT NULL"))

    session = SessionLocal()
    try:
        rows = session.query(UploadFile).filter(UploadFile.folder_key.is_(None)).all()
        changed = False
        for row in rows:
            next_folder_key = _compute_folder_key_for_row(row)
            if row.folder_key != next_folder_key:
                row.folder_key = next_folder_key
                meta = row.meta if isinstance(row.meta, dict) else {}
                rule = get_rule_for_filename(row.original_filename or "")
                meta_kind = meta.get("kind") if isinstance(meta.get("kind"), str) else None
                meta_mode = meta.get("mode") if isinstance(meta.get("mode"), str) else None
                row.meta = {
                    **meta,
                    "kind": meta_kind or (rule.kind if rule else "3d"),
                    "mode": meta_mode or (rule.mode if rule else "brep"),
                    "project_id": str(meta.get("project_id") or "default"),
                }
                changed = True
        if changed:
            session.commit()
    finally:
        session.close()


def _ensure_rule_configs() -> None:
    session = SessionLocal()
    try:
        seed_default_rule_configs(session)
    finally:
        session.close()


def _ensure_master_contract_schema() -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS tenants (
                    id BIGSERIAL PRIMARY KEY,
                    code VARCHAR(128) NOT NULL UNIQUE,
                    name VARCHAR(255) NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS memberships (
                    id BIGSERIAL PRIMARY KEY,
                    tenant_id BIGINT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    role VARCHAR(64) NOT NULL DEFAULT 'member',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    UNIQUE (tenant_id, user_id)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS plans (
                    id BIGSERIAL PRIMARY KEY,
                    code VARCHAR(128) NOT NULL UNIQUE,
                    name VARCHAR(255) NOT NULL,
                    limits_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id BIGSERIAL PRIMARY KEY,
                    tenant_id BIGINT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
                    plan_id BIGINT NOT NULL REFERENCES plans(id) ON DELETE RESTRICT,
                    status VARCHAR(64) NOT NULL DEFAULT 'active',
                    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    ends_at TIMESTAMPTZ,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS files (
                    id VARCHAR(40) PRIMARY KEY,
                    file_id VARCHAR(40) NOT NULL UNIQUE,
                    uploaded_file_id VARCHAR(40) UNIQUE,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    CONSTRAINT ck_files_id_equals_file_id CHECK (id = file_id),
                    CONSTRAINT fk_files_uploaded_file FOREIGN KEY (uploaded_file_id)
                        REFERENCES uploaded_files(file_id) ON DELETE SET NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS file_versions (
                    id BIGSERIAL PRIMARY KEY,
                    file_id VARCHAR(40) NOT NULL REFERENCES files(id) ON DELETE CASCADE,
                    version_no INTEGER NOT NULL,
                    uploaded_file_id VARCHAR(40),
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    UNIQUE (file_id, version_no)
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS job_logs (
                    id BIGSERIAL PRIMARY KEY,
                    job_id TEXT,
                    file_id VARCHAR(40),
                    stage VARCHAR(64),
                    message TEXT NOT NULL,
                    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO files (id, file_id, uploaded_file_id, created_at, updated_at)
                SELECT uf.file_id, uf.file_id, uf.file_id, COALESCE(uf.created_at, now()), COALESCE(uf.updated_at, now())
                FROM uploaded_files uf
                ON CONFLICT (id) DO NOTHING
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO file_versions (file_id, version_no, uploaded_file_id, created_at)
                SELECT uf.file_id, 1, uf.file_id, COALESCE(uf.created_at, now())
                FROM uploaded_files uf
                ON CONFLICT (file_id, version_no) DO NOTHING
                """
            )
        )


def register_startup(app: FastAPI) -> None:
    @app.on_event("startup")
    def _create_all() -> None:
        # Ensure models are imported before metadata create_all.
        from app.models import core as _core  # noqa: F401
        from app.models import file as _file  # noqa: F401
        from app.models import library_item as _library_item  # noqa: F401
        from app.models import orchestrator as _orchestrator  # noqa: F401
        Base.metadata.create_all(bind=engine)
        _ensure_uploaded_files_schema()
        _ensure_master_contract_schema()
        _ensure_rule_configs()
        ensure_bucket_exists(settings)
