from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass(frozen=True)
class RuntimeContext:
    tenant_id: str
    project_id: str
    principal_type: str
    principal_id: str
    session_id: str
    trace_id: str
    file_ids: tuple[str, ...] = ()
    allowed_tools: frozenset[str] = frozenset()


@dataclass
class RuntimeRequest:
    message: str
    context: RuntimeContext
    top_k: int = 6
    tool_requests: list[dict[str, Any]] = field(default_factory=list)
    metadata_filters: dict[str, Any] = field(default_factory=dict)


@dataclass
class RuntimeEvent:
    event_type: str
    agent: str
    payload: dict[str, Any]
    at: str = field(default_factory=now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "agent": self.agent,
            "payload": self.payload,
            "at": self.at,
        }


@dataclass
class PlanNode:
    node_id: str
    kind: str
    description: str
    depends_on: tuple[str, ...] = ()
    payload: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "kind": self.kind,
            "description": self.description,
            "depends_on": list(self.depends_on),
            "payload": self.payload,
        }


@dataclass
class TaskGraph:
    graph_id: str
    nodes: list[PlanNode]
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create(cls, nodes: list[PlanNode], metadata: dict[str, Any] | None = None) -> "TaskGraph":
        return cls(graph_id=f"tg_{uuid4().hex[:16]}", nodes=nodes, metadata=metadata or {})

    def to_dict(self) -> dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "nodes": [node.to_dict() for node in self.nodes],
            "metadata": self.metadata,
        }


@dataclass
class RetrievalChunk:
    chunk_id: str
    source_type: str
    source_ref: str
    text: str
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "source_type": self.source_type,
            "source_ref": self.source_ref,
            "text": self.text,
            "score": round(float(self.score), 6),
            "metadata": self.metadata,
        }


@dataclass
class RetrievalResult:
    query: str
    chunks: list[RetrievalChunk]
    embedding_dim: int
    filtered_out: int = 0
    used_sources: tuple[str, ...] = ()

    @property
    def top_score(self) -> float:
        if not self.chunks:
            return 0.0
        return float(self.chunks[0].score)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "embedding_dim": self.embedding_dim,
            "filtered_out": self.filtered_out,
            "used_sources": list(self.used_sources),
            "chunks": [chunk.to_dict() for chunk in self.chunks],
        }


@dataclass
class ToolExecution:
    tool_name: str
    status: str
    output: dict[str, Any] = field(default_factory=dict)
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "status": self.status,
            "output": self.output,
            "reason": self.reason,
        }


@dataclass
class MemorySnapshot:
    session: list[dict[str, Any]] = field(default_factory=list)
    working: list[dict[str, Any]] = field(default_factory=list)
    long_term: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session": self.session,
            "working": self.working,
            "long_term": self.long_term,
        }


@dataclass
class RuntimeResponse:
    session_id: str
    trace_id: str
    reply: str
    plan: TaskGraph
    retrieval: RetrievalResult
    tool_results: list[ToolExecution]
    memory: MemorySnapshot
    events: list[RuntimeEvent]

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "trace_id": self.trace_id,
            "reply": self.reply,
            "plan": self.plan.to_dict(),
            "retrieval": self.retrieval.to_dict(),
            "tool_results": [item.to_dict() for item in self.tool_results],
            "memory": self.memory.to_dict(),
            "events": [event.to_dict() for event in self.events],
        }
