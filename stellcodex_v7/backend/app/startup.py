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
        conn.execute(text("ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS tenant_id BIGINT"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_uploaded_files_tenant_id ON uploaded_files (tenant_id)"))
        conn.execute(text("ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS folder_key TEXT"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_uploaded_files_folder_key ON uploaded_files (folder_key)"))
        conn.execute(text("ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS decision_json JSONB"))
        conn.execute(text("UPDATE uploaded_files SET decision_json = '{}'::jsonb WHERE decision_json IS NULL"))
        conn.execute(text("ALTER TABLE uploaded_files ALTER COLUMN decision_json SET NOT NULL"))
        conn.execute(
            text(
                """
                INSERT INTO tenants (code, name, created_at, updated_at)
                SELECT DISTINCT
                    'owner-' || substr(md5(coalesce(owner_sub, 'anonymous')), 1, 24) AS code,
                    'Owner ' || substr(md5(coalesce(owner_sub, 'anonymous')), 1, 12) AS name,
                    now() AS created_at,
                    now() AS updated_at
                FROM uploaded_files
                ON CONFLICT (code) DO NOTHING
                """
            )
        )
        conn.execute(
            text(
                """
                UPDATE uploaded_files uf
                SET tenant_id = t.id
                FROM tenants t
                WHERE uf.tenant_id IS NULL
                  AND t.code = 'owner-' || substr(md5(coalesce(uf.owner_sub, 'anonymous')), 1, 24)
                """
            )
        )
        conn.execute(
            text(
                """
                UPDATE uploaded_files
                SET status = 'failed',
                    metadata = jsonb_set(
                        jsonb_set(COALESCE(metadata::jsonb, '{}'::jsonb), '{error_code}', to_jsonb('ASSEMBLY_META_MISSING'::text), true),
                        '{error}',
                        to_jsonb('assembly_meta and preview artifacts are mandatory for ready status'::text),
                        true
                    )::json
                WHERE lower(status) = 'ready'
                  AND coalesce((metadata::jsonb ->> 'kind'), '3d') = '3d'
                  AND (
                    NOT (metadata::jsonb ? 'assembly_meta')
                    OR jsonb_typeof(metadata::jsonb -> 'assembly_meta') <> 'object'
                    OR NOT (metadata::jsonb ? 'assembly_meta_key')
                  )
                """
            )
        )
        conn.execute(text("ALTER TABLE uploaded_files ALTER COLUMN tenant_id SET NOT NULL"))
        conn.execute(
            text(
                """
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1
                        FROM pg_constraint
                        WHERE conname = 'fk_uploaded_files_tenant'
                    ) THEN
                        ALTER TABLE uploaded_files
                        ADD CONSTRAINT fk_uploaded_files_tenant
                        FOREIGN KEY (tenant_id) REFERENCES tenants(id);
                    END IF;
                END
                $$;
                """
            )
        )

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
        conn.execute(text("ALTER TABLE files ADD COLUMN IF NOT EXISTS id VARCHAR(40)"))
        conn.execute(text("ALTER TABLE files ADD COLUMN IF NOT EXISTS file_id VARCHAR(40)"))
        conn.execute(text("ALTER TABLE files ADD COLUMN IF NOT EXISTS uploaded_file_id VARCHAR(40)"))
        conn.execute(text("ALTER TABLE files ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now()"))
        conn.execute(text("ALTER TABLE files ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now()"))
        conn.execute(text("UPDATE files SET file_id = COALESCE(file_id, id) WHERE file_id IS NULL"))
        conn.execute(text("UPDATE files SET id = file_id WHERE id IS NULL AND file_id IS NOT NULL"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_files_file_id ON files (file_id)"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_files_uploaded_file_id ON files (uploaded_file_id)"))
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
        conn.execute(text("ALTER TABLE file_versions ADD COLUMN IF NOT EXISTS uploaded_file_id VARCHAR(40)"))
        conn.execute(text("ALTER TABLE file_versions ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now()"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_file_versions_file_ver ON file_versions (file_id, version_no)"))
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
        conn.execute(text("ALTER TABLE job_logs ADD COLUMN IF NOT EXISTS payload JSONB NOT NULL DEFAULT '{}'::jsonb"))
        conn.execute(text("ALTER TABLE job_logs ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now()"))
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


def _ensure_knowledge_schema() -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS knowledge_records (
                    id UUID PRIMARY KEY,
                    record_id VARCHAR(64) NOT NULL UNIQUE,
                    tenant_id BIGINT NOT NULL,
                    project_id VARCHAR(128),
                    file_id VARCHAR(40),
                    source_type VARCHAR(64) NOT NULL,
                    source_subtype VARCHAR(64) NOT NULL,
                    source_ref TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    text TEXT NOT NULL,
                    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                    tags_json JSONB NOT NULL DEFAULT '[]'::jsonb,
                    security_class VARCHAR(32) NOT NULL DEFAULT 'internal',
                    hash_sha256 VARCHAR(64) NOT NULL,
                    index_version VARCHAR(32) NOT NULL DEFAULT 'v1',
                    embedding_status VARCHAR(24) NOT NULL DEFAULT 'pending',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    CONSTRAINT ux_knowledge_records_source_hash UNIQUE (tenant_id, source_ref, hash_sha256, index_version)
                )
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_knowledge_records_tenant_id ON knowledge_records (tenant_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_knowledge_records_project_id ON knowledge_records (project_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_knowledge_records_file_id ON knowledge_records (file_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_knowledge_records_source_type ON knowledge_records (source_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_knowledge_records_record_id ON knowledge_records (record_id)"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS knowledge_index_jobs (
                    id UUID PRIMARY KEY,
                    event_id VARCHAR(64),
                    event_type VARCHAR(64),
                    tenant_id BIGINT,
                    project_id VARCHAR(128),
                    file_id VARCHAR(40),
                    source_ref TEXT,
                    status VARCHAR(24) NOT NULL DEFAULT 'pending',
                    failure_code VARCHAR(64),
                    error_detail TEXT,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_knowledge_index_jobs_event_id ON knowledge_index_jobs (event_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_knowledge_index_jobs_event_type ON knowledge_index_jobs (event_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_knowledge_index_jobs_tenant_id ON knowledge_index_jobs (tenant_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_knowledge_index_jobs_project_id ON knowledge_index_jobs (project_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_knowledge_index_jobs_file_id ON knowledge_index_jobs (file_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_knowledge_index_jobs_status ON knowledge_index_jobs (status)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_knowledge_index_jobs_failure_code ON knowledge_index_jobs (failure_code)"))


def _ensure_engineering_schema() -> None:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE artifact_manifest ADD COLUMN IF NOT EXISTS geometry_hash VARCHAR(64)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_artifact_manifest_geometry_hash ON artifact_manifest (geometry_hash)"))


def register_startup(app: FastAPI) -> None:
    @app.on_event("startup")
    def _create_all() -> None:
        # Ensure models are imported before metadata create_all.
        from app.models import core as _core  # noqa: F401
        from app.models import file as _file  # noqa: F401
        from app.models import phase2 as _phase2  # noqa: F401
        from app.models import engineering as _engineering  # noqa: F401
        from app.models import library_item as _library_item  # noqa: F401
        from app.models import master_contract as _master_contract  # noqa: F401
        from app.models import orchestrator as _orchestrator  # noqa: F401
        from app.models import knowledge as _knowledge  # noqa: F401
        Base.metadata.create_all(bind=engine)
        _ensure_uploaded_files_schema()
        _ensure_master_contract_schema()
        _ensure_knowledge_schema()
        _ensure_engineering_schema()
        _ensure_rule_configs()
        ensure_bucket_exists(settings)
