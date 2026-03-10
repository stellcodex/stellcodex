"""Typed event publishers for common STELLCODEX event types."""
from __future__ import annotations

from typing import Any

from app.events.bus import AgentEventBus, get_agent_event_bus
from app.events.cloudevents import CloudEvent


def publish_task_submitted(
    bus: AgentEventBus,
    *,
    task_id: str,
    tenant_id: str,
    project_id: str,
    goal: str,
    trace_id: str,
) -> str:
    event = CloudEvent.build(
        event_type="agent.task.submitted",
        source="api.stell_ai.tasks",
        subject=f"task:{task_id}",
        tenant_id=tenant_id,
        project_id=project_id,
        trace_id=trace_id,
        data={"task_id": task_id, "goal": goal},
    )
    return bus.publish(event)


def publish_task_planned(
    bus: AgentEventBus,
    *,
    task_id: str,
    tenant_id: str,
    project_id: str,
    step_count: int,
    risk_level: str,
    trace_id: str,
) -> str:
    event = CloudEvent.build(
        event_type="agent.task.planned",
        source="stell_ai.planner",
        subject=f"task:{task_id}",
        tenant_id=tenant_id,
        project_id=project_id,
        trace_id=trace_id,
        data={"task_id": task_id, "step_count": step_count, "risk_level": risk_level},
    )
    return bus.publish(event)


def publish_task_completed(
    bus: AgentEventBus,
    *,
    task_id: str,
    tenant_id: str,
    project_id: str,
    success: bool,
    trace_id: str,
) -> str:
    event = CloudEvent.build(
        event_type="agent.task.completed",
        source="stell_ai.executor",
        subject=f"task:{task_id}",
        tenant_id=tenant_id,
        project_id=project_id,
        trace_id=trace_id,
        data={"task_id": task_id, "success": success},
    )
    return bus.publish(event)


def publish_event_ingested(
    bus: AgentEventBus,
    *,
    event_id: str,
    event_type: str,
    tenant_id: str,
    project_id: str,
    trace_id: str,
) -> str:
    event = CloudEvent.build(
        event_type="agent.event.ingested",
        source="api.stell_ai.events",
        subject=f"event:{event_id}",
        tenant_id=tenant_id,
        project_id=project_id,
        trace_id=trace_id,
        data={"ingested_event_id": event_id, "ingested_event_type": event_type},
    )
    return bus.publish(event)
