from fastapi import FastAPI
from sqlalchemy import text

from app.db import Base, engine
from app.db.session import SessionLocal
from app.models.file import UploadFile
from app.core.format_registry import get_rule_for_filename


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


def register_startup(app: FastAPI) -> None:
    @app.on_event("startup")
    def _create_all() -> None:
        # Ensure models are imported before metadata create_all.
        from app.models import core as _core  # noqa: F401
        from app.models import file as _file  # noqa: F401
        Base.metadata.create_all(bind=engine)
        _ensure_uploaded_files_schema()
