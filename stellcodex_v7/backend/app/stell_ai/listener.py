"""Listener — event ingestion and task submission handler.

Generates event_id, task_id, trace_id.
Normalizes payloads into CloudEvent schema.
Stores every event in audit trail.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.events.bus import get_agent_event_bus
from app.events.cloudevents import CloudEvent
from app.events.idempotency import ensure_idempotent
from app.events.publishers import publish_event_ingested
from app.services.audit import log_event
from app.stell_ai.models import AgentTask

log = logging.getLogger(__name__)


def ingest_event(
    db: Session,
    *,
    event_type: str,
    source: str,
    subject: str,
    tenant_id: str,
    project_id: str,
    data: dict[str, Any],
    trace_id: str | None = None,
    event_id: str | None = None,
) -> tuple[CloudEvent, bool]:
    """Normalize and ingest an event. Returns (event, was_duplicate)."""
    event = CloudEvent.build(
        event_type=event_type,
        source=source,
        subject=subject,
        tenant_id=tenant_id,
        project_id=project_id,
        data=data,
        trace_id=trace_id,
        event_id=event_id,
    )

    duplicate = ensure_idempotent(db, event.id, event.type)
    if duplicate:
        log.debug("listener.duplicate event_id=%s", event.id)
        return event, True

    # Audit trail
    try:
        log_event(
            db=db,
            action=f"event.ingested:{event.type}",
            actor="system:listener",
            resource=event.subject,
            detail={
                "event_id": event.id,
                "event_type": event.type,
                "source": event.source,
                "tenant_id": event.tenant_id,
                "project_id": event.project_id,
            },
        )
    except Exception as exc:
        log.warning("listener.audit_failed: %s", exc)

    # Publish to event bus
    try:
        bus = get_agent_event_bus()
        publish_event_ingested(
            bus,
            event_id=event.id,
            event_type=event.type,
            tenant_id=event.tenant_id,
            project_id=event.project_id,
            trace_id=event.trace_id,
        )
    except Exception as exc:
        log.warning("listener.bus_publish_failed: %s", exc)

    return event, False


def submit_task(
    db: Session,
    *,
    goal: str,
    tenant_id: str,
    project_id: str,
    trace_id: str,
    file_ids: list[str] | None = None,
    allowed_tools: frozenset[str] | None = None,
    execute: bool = True,
) -> AgentTask:
    """Create and optionally execute an agent task."""
    task_id = f"task_{uuid.uuid4().hex[:16]}"
    task = AgentTask(
        id=uuid.uuid4(),
        task_id=task_id,
        tenant_id=int(tenant_id) if tenant_id.isdigit() else 0,
        project_id=project_id,
        trace_id=trace_id,
        goal=goal,
        status="pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    db.add(task)
    db.flush()

    if execute:
        _execute_task(db, task=task, file_ids=file_ids or [], allowed_tools=allowed_tools or frozenset())

    return task


def _execute_task(
    db: Session,
    *,
    task: AgentTask,
    file_ids: list[str],
    allowed_tools: frozenset[str],
) -> None:
    """Build plan, execute steps, generate report, update task."""
    from app.stell_ai.planner import build_plan
    from app.stell_ai.executor import execute_plan
    from app.stell_ai.reporter import generate_report
    from app.events.bus import get_agent_event_bus
    from app.events.publishers import publish_task_submitted, publish_task_planned, publish_task_completed

    bus = get_agent_event_bus()
    tenant_id = str(task.tenant_id)
    project_id = str(task.project_id or "default")

    publish_task_submitted(
        bus,
        task_id=task.task_id,
        tenant_id=tenant_id,
        project_id=project_id,
        goal=task.goal,
        trace_id=task.trace_id,
    )

    try:
        plan = build_plan(
            goal=task.goal,
            file_ids=file_ids,
            allowed_tools=allowed_tools or None,
        )
        task.plan_json = {
            "goal": plan.goal,
            "risk_level": plan.risk_level,
            "requires_approval": plan.requires_approval,
            "steps": [s.model_dump() for s in plan.steps],
            "context_refs": plan.context_refs,
        }
        task.risk_level = plan.risk_level
        task.requires_approval = "true" if plan.requires_approval else "false"
        task.status = "planned"

        publish_task_planned(
            bus,
            task_id=task.task_id,
            tenant_id=tenant_id,
            project_id=project_id,
            step_count=len(plan.steps),
            risk_level=plan.risk_level,
            trace_id=task.trace_id,
        )

        context = {
            "tenant_id": tenant_id,
            "project_id": project_id,
            "task_id": task.task_id,
        }
        executed, failed = execute_plan(
            plan,
            context=context,
            allowed_tools=allowed_tools or frozenset(),
        )

        result = generate_report(
            task_id=task.task_id,
            goal=task.goal,
            status="completed" if not failed else "partial",
            plan=plan,
            executed_steps=executed,
            failed_steps=failed,
        )

        task.result_json = result.report_json
        task.status = result.status
        task.updated_at = datetime.utcnow()

        publish_task_completed(
            bus,
            task_id=task.task_id,
            tenant_id=tenant_id,
            project_id=project_id,
            success=(task.status == "completed"),
            trace_id=task.trace_id,
        )

    except Exception as exc:
        log.error("listener.task_execution_failed task_id=%s: %s", task.task_id, exc)
        task.status = "failed"
        task.error_detail = str(exc)
        task.updated_at = datetime.utcnow()
