from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import settings
from app.db import Base, engine
from app.db.session import SessionLocal
from app.models.file import UploadFile
from app.models.user import User
from app.core.format_registry import get_rule_for_filename
from app.services.auth_access import ensure_seed_users, normalize_auth_provider, normalize_role


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


def _ensure_users_schema() -> None:
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name TEXT"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_provider VARCHAR(32) NOT NULL DEFAULT 'local'"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS google_sub TEXT"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP"))
        conn.execute(text("UPDATE users SET role = 'member' WHERE role IS NULL OR role = 'user'"))
        conn.execute(text("UPDATE users SET auth_provider = COALESCE(NULLIF(auth_provider, ''), 'local')"))
        conn.execute(text("UPDATE users SET is_active = NOT COALESCE(is_suspended, FALSE)"))
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ux_users_google_sub ON users (google_sub) WHERE google_sub IS NOT NULL"))

    session = SessionLocal()
    try:
        rows = session.query(User).all()
        changed = False
        for row in rows:
            next_role = normalize_role(row.role)
            next_provider = normalize_auth_provider(row.auth_provider)
            next_is_active = not bool(row.is_suspended)
            if row.role != next_role:
                row.role = next_role
                changed = True
            if row.auth_provider != next_provider:
                row.auth_provider = next_provider
                changed = True
            if row.is_active != next_is_active:
                row.is_active = next_is_active
                changed = True
        if changed:
            session.commit()
        ensure_seed_users(session)
    finally:
        session.close()


def _ensure_stell_ai_memory_schema() -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS experience_ledger (
                  id UUID PRIMARY KEY,
                  task_query TEXT NOT NULL,
                  successful_plan JSONB NOT NULL DEFAULT '{}'::jsonb,
                  lessons_learned TEXT NULL,
                  feedback_from_owner TEXT NULL,
                  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS decision_logs (
                  decision_id UUID PRIMARY KEY,
                  prompt TEXT NOT NULL,
                  lane VARCHAR(64) NOT NULL,
                  executor VARCHAR(128) NOT NULL,
                  decision_json JSONB NOT NULL DEFAULT '{}'::jsonb,
                  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        )
        conn.execute(
            text(
                "ALTER TABLE ai_case_logs ADD COLUMN IF NOT EXISTS "
                "retrieved_context_summary JSONB NULL"
            )
        )


def register_startup(app: FastAPI) -> None:
    @app.on_event("startup")
    def _create_all() -> None:
        # Ensure models are imported before metadata create_all.
        from app.models import core as _core  # noqa: F401
        from app.models import file as _file  # noqa: F401
        from app.models import file_version as _file_version  # noqa: F401
        from app.models import library_item as _library_item  # noqa: F401
        from app.models import orchestrator as _orchestrator  # noqa: F401
        from app.models import ai_learning as _ai_learning  # noqa: F401
        from app.models import rule_config as _rule_config  # noqa: F401
        Base.metadata.create_all(bind=engine)
        _ensure_users_schema()
        _ensure_uploaded_files_schema()
        _ensure_stell_ai_memory_schema()
