from __future__ import annotations

from sqlalchemy.orm import configure_mappers


def prepare_worker_runtime() -> None:
    # Preload ORM models so the first queued job does not spend its timeout budget
    # on lazy mapper configuration.
    from app.models import ai_learning as _ai_learning  # noqa: F401
    from app.models import core as _core  # noqa: F401
    from app.models import file as _file  # noqa: F401
    from app.models import file_version as _file_version  # noqa: F401
    from app.models import library_item as _library_item  # noqa: F401
    from app.models import orchestrator as _orchestrator  # noqa: F401
    from app.models import rule_config as _rule_config  # noqa: F401

    configure_mappers()
