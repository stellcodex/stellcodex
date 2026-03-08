from __future__ import annotations

from typing import Callable

from app.core.event_bus import EventBus
from app.stellai.types import RuntimeContext, RuntimeEvent


class RuntimeEventHub:
    def __init__(self, sink: Callable[[RuntimeEvent], None] | None = None) -> None:
        self._sink = sink
        self._events: list[RuntimeEvent] = []

    @property
    def events(self) -> list[RuntimeEvent]:
        return list(self._events)

    def emit(self, event: RuntimeEvent) -> None:
        self._events.append(event)
        if self._sink is not None:
            self._sink(event)


def _to_phase2_event_type(event: RuntimeEvent) -> str:
    return f"stellai.{event.agent}.{event.event_type}"


def phase2_event_sink(event_bus: EventBus, context: RuntimeContext) -> Callable[[RuntimeEvent], None]:
    def _sink(event: RuntimeEvent) -> None:
        event_bus.publish_event(
            event_type=_to_phase2_event_type(event),
            source=f"stellai.{event.agent}",
            subject=context.session_id,
            tenant_id=context.tenant_id,
            project_id=context.project_id,
            trace_id=context.trace_id,
            data=event.to_dict(),
        )

    return _sink
