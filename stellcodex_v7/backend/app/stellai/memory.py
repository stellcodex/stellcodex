from __future__ import annotations

import json
import re
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.stellai.types import MemorySnapshot, RuntimeContext

TOKEN_RE = re.compile(r"[a-z0-9_]+")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _tokenize(text: str) -> set[str]:
    return set(TOKEN_RE.findall((text or "").lower()))


def _score(query: str, text: str) -> float:
    q = _tokenize(query)
    t = _tokenize(text)
    if not q or not t:
        return 0.0
    overlap = len(q & t)
    return overlap / max(1, len(q))


@dataclass
class MemoryEntry:
    tenant_id: str
    project_id: str
    session_id: str
    role: str
    text: str
    created_at: str = field(default_factory=_now_iso)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "project_id": self.project_id,
            "session_id": self.session_id,
            "role": self.role,
            "text": self.text,
            "created_at": self.created_at,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MemoryEntry":
        return cls(
            tenant_id=str(payload.get("tenant_id") or "0"),
            project_id=str(payload.get("project_id") or "default"),
            session_id=str(payload.get("session_id") or "session"),
            role=str(payload.get("role") or "system"),
            text=str(payload.get("text") or ""),
            created_at=str(payload.get("created_at") or _now_iso()),
            metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
        )


class SessionMemoryStore:
    def __init__(self, max_messages: int = 30) -> None:
        self.max_messages = max(4, int(max_messages))
        self._entries: dict[tuple[str, str], deque[MemoryEntry]] = defaultdict(lambda: deque(maxlen=self.max_messages))

    def append(self, entry: MemoryEntry) -> None:
        self._entries[(entry.tenant_id, entry.session_id)].append(entry)

    def get(self, tenant_id: str, session_id: str) -> list[dict[str, Any]]:
        return [item.to_dict() for item in self._entries[(tenant_id, session_id)]]


class WorkingMemoryStore:
    def __init__(self, window_size: int = 8) -> None:
        self.window_size = max(2, int(window_size))
        self._entries: dict[tuple[str, str], deque[MemoryEntry]] = defaultdict(lambda: deque(maxlen=self.window_size))

    def append(self, entry: MemoryEntry) -> None:
        self._entries[(entry.tenant_id, entry.session_id)].append(entry)

    def get(self, tenant_id: str, session_id: str) -> list[dict[str, Any]]:
        return [item.to_dict() for item in self._entries[(tenant_id, session_id)]]


class LongTermMemoryStore:
    def __init__(self, root: str | Path = "/root/workspace/_truth/records/stell_ai_long_term") -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _tenant_path(self, tenant_id: str, project_id: str) -> Path:
        safe_project = re.sub(r"[^a-zA-Z0-9_.-]+", "_", project_id or "default")
        tenant_dir = self.root / f"tenant_{tenant_id}"
        tenant_dir.mkdir(parents=True, exist_ok=True)
        return tenant_dir / f"{safe_project}.jsonl"

    def append(self, entry: MemoryEntry) -> Path:
        path = self._tenant_path(entry.tenant_id, entry.project_id)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
        return path

    def search(self, tenant_id: str, project_id: str, query: str, limit: int = 6) -> list[dict[str, Any]]:
        path = self._tenant_path(tenant_id, project_id)
        if not path.exists():
            return []
        scored: list[tuple[float, dict[str, Any]]] = []
        for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue
            if str(payload.get("tenant_id") or "") != str(tenant_id):
                continue
            text = str(payload.get("text") or "")
            rank = _score(query, text)
            if rank <= 0:
                continue
            scored.append((rank, payload))
        scored.sort(key=lambda item: item[0], reverse=True)
        return [payload for _rank, payload in scored[: max(1, int(limit))]]


class MemoryManager:
    def __init__(
        self,
        *,
        session_store: SessionMemoryStore | None = None,
        working_store: WorkingMemoryStore | None = None,
        long_term_store: LongTermMemoryStore | None = None,
    ) -> None:
        self.session_store = session_store or SessionMemoryStore()
        self.working_store = working_store or WorkingMemoryStore()
        self.long_term_store = long_term_store or LongTermMemoryStore()

    def load(self, *, context: RuntimeContext, query: str) -> MemorySnapshot:
        return MemorySnapshot(
            session=self.session_store.get(context.tenant_id, context.session_id),
            working=self.working_store.get(context.tenant_id, context.session_id),
            long_term=self.long_term_store.search(
                context.tenant_id,
                context.project_id,
                query,
                limit=6,
            ),
        )

    def append_user_turn(self, *, context: RuntimeContext, text: str, metadata: dict[str, Any] | None = None) -> None:
        entry = MemoryEntry(
            tenant_id=context.tenant_id,
            project_id=context.project_id,
            session_id=context.session_id,
            role="user",
            text=text,
            metadata=metadata or {},
        )
        self.session_store.append(entry)
        self.working_store.append(entry)

    def append_stell_turn(
        self,
        *,
        context: RuntimeContext,
        text: str,
        metadata: dict[str, Any] | None = None,
        persist_long_term: bool = True,
    ) -> Path | None:
        entry = MemoryEntry(
            tenant_id=context.tenant_id,
            project_id=context.project_id,
            session_id=context.session_id,
            role="stell_ai",
            text=text,
            metadata=metadata or {},
        )
        self.session_store.append(entry)
        self.working_store.append(entry)
        if not persist_long_term:
            return None
        return self.long_term_store.append(entry)
