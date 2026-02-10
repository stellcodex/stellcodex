from fastapi import FastAPI

from app.db import Base, engine


def register_startup(app: FastAPI) -> None:
    @app.on_event("startup")
    def _create_all() -> None:
        # Ensure models are imported before metadata create_all.
        from app.models import core as _core  # noqa: F401
        from app.models import file as _file  # noqa: F401
        Base.metadata.create_all(bind=engine)
