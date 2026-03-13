from __future__ import annotations

import os
import platform
import socket
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.engineering import WorkerNode


_VALID_STATUSES = {"online", "busy", "offline", "draining", "disabled"}


def _normalize_status(value: str | None) -> str:
    token = str(value or "online").strip().lower()
    return token if token in _VALID_STATUSES else "online"


def _detect_ram_mb() -> int | None:
    try:
        page_size = int(os.sysconf("SC_PAGE_SIZE"))
        pages = int(os.sysconf("SC_PHYS_PAGES"))
        total = (page_size * pages) // (1024 * 1024)
        return total if total > 0 else None
    except (AttributeError, OSError, ValueError):
        return None


def build_local_worker_snapshot(*, queues: list[str] | tuple[str, ...]) -> dict[str, Any]:
    hostname = socket.gethostname()
    worker_id = str(os.getenv("STELLCODEX_WORKER_ID") or f"{hostname}:{os.getpid()}")
    return {
        "worker_id": worker_id,
        "provider": str(os.getenv("STELLCODEX_WORKER_PROVIDER") or "local"),
        "region": str(os.getenv("STELLCODEX_WORKER_REGION") or "") or None,
        "cpu": os.cpu_count(),
        "ram_mb": _detect_ram_mb(),
        "gpu_enabled": str(os.getenv("STELLCODEX_WORKER_GPU", "")).strip().lower() in {"1", "true", "yes", "y"},
        "capabilities": {
            "queues": list(queues),
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "status": "online",
        "version": str(os.getenv("STELLCODEX_WORKER_VERSION") or "v7"),
        "metadata": {"pid": os.getpid(), "hostname": hostname},
    }


def upsert_worker_node(
    db: Session,
    *,
    worker_id: str,
    provider: str,
    region: str | None = None,
    cpu: int | None = None,
    ram_mb: int | None = None,
    gpu_enabled: bool = False,
    capabilities: dict[str, Any] | None = None,
    status: str = "online",
    version: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> WorkerNode:
    row = db.query(WorkerNode).filter(WorkerNode.worker_id == str(worker_id)).first()
    if row is None:
        row = WorkerNode(worker_id=str(worker_id))
    row.provider = str(provider or "unknown")
    row.region = str(region or "") or None
    row.cpu = int(cpu) if cpu is not None else None
    row.ram_mb = int(ram_mb) if ram_mb is not None else None
    row.gpu_enabled = bool(gpu_enabled)
    row.capabilities_json = capabilities if isinstance(capabilities, dict) else {}
    row.status = _normalize_status(status)
    row.version = str(version or "") or None
    row.metadata_json = metadata if isinstance(metadata, dict) else {}
    row.last_heartbeat = datetime.utcnow()
    db.add(row)
    return row


def heartbeat_worker_node(db: Session, *, worker_id: str, status: str | None = None) -> WorkerNode | None:
    row = db.query(WorkerNode).filter(WorkerNode.worker_id == str(worker_id)).first()
    if row is None:
        return None
    row.last_heartbeat = datetime.utcnow()
    if status is not None:
        row.status = _normalize_status(status)
    db.add(row)
    return row


def set_worker_status(db: Session, *, worker_id: str, status: str) -> WorkerNode | None:
    row = db.query(WorkerNode).filter(WorkerNode.worker_id == str(worker_id)).first()
    if row is None:
        return None
    row.status = _normalize_status(status)
    row.last_heartbeat = datetime.utcnow()
    db.add(row)
    return row
