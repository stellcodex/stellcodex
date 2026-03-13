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
from app.stell_ai.policy import classify_risk, requires_approval
from app.stellai.service import get_stellai_runtime
from app.stellai.types import RuntimeContext, RuntimeRequest, RuntimeResponse

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

    version_no: int | None = None
    raw_version = data.get("version_no")
    if raw_version is not None:
        try:
            version_no = int(raw_version)
        except (TypeError, ValueError):
            version_no = None

    duplicate = ensure_idempotent(
        db,
        event.id,
        event.type,
        consumer="stellai.listener",
        file_id=str(data.get("file_id") or "") or None,
        version_no=version_no,
        trace_id=event.trace_id,
        payload=event.to_dict(),
    )
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
    """Execute legacy AgentTask flow through the primary STELLAI runtime."""
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
        runtime_request = _build_runtime_request(
            task=task,
            file_ids=file_ids,
            allowed_tools=allowed_tools,
        )
        runtime = get_stellai_runtime()
        runtime_result = runtime.run(request=runtime_request, db=db)

        _apply_runtime_result_to_task(task=task, runtime_result=runtime_result)

        publish_task_planned(
            bus,
            task_id=task.task_id,
            tenant_id=tenant_id,
            project_id=project_id,
            step_count=len(task.plan_json.get("steps") or []) if isinstance(task.plan_json, dict) else 0,
            risk_level=str(task.risk_level or "low"),
            trace_id=task.trace_id,
        )
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


def _build_runtime_request(
    *,
    task: AgentTask,
    file_ids: list[str],
    allowed_tools: frozenset[str],
) -> RuntimeRequest:
    context = RuntimeContext(
        tenant_id=str(task.tenant_id),
        project_id=str(task.project_id or "default"),
        principal_type="service",
        principal_id="agent_task_listener",
        session_id=str(task.task_id),
        trace_id=str(task.trace_id),
        file_ids=tuple(str(item) for item in file_ids if str(item).strip()),
        allowed_tools=allowed_tools or frozenset(),
    )
    return RuntimeRequest(
        message=str(task.goal),
        context=context,
        top_k=6,
        metadata_filters={"project_id": str(task.project_id or "default")},
    )


def _apply_runtime_result_to_task(*, task: AgentTask, runtime_result: RuntimeResponse) -> None:
    planned_tools = _planned_tools_from_response(runtime_result)
    risk_level = classify_risk(task.goal, planned_tools)
    approval_required = requires_approval(risk_level)
    plan_steps = [
        {
            "step_id": f"step_{index:03d}",
            "tool": tool_name,
            "arguments": {},
            "requires_approval": approval_required,
            "rollback_note": "Runtime execution is read-only and fail-closed.",
        }
        for index, tool_name in enumerate(planned_tools, start=1)
    ]
    executed_steps: list[dict[str, Any]] = []
    failed_steps: list[dict[str, Any]] = []
    evidence_refs: list[str] = []

    for index, item in enumerate(runtime_result.tool_results, start=1):
        evidence_ref = _extract_evidence_ref(item.output)
        if evidence_ref:
            evidence_refs.append(evidence_ref)
        step_payload = {
            "step_id": f"step_{index:03d}",
            "tool": item.tool_name,
            "success": item.status == "ok",
            "output": item.output,
            "error": item.reason,
            "evidence_ref": evidence_ref,
        }
        if item.status == "ok":
            executed_steps.append(step_payload)
        else:
            failed_steps.append(step_payload)

    for chunk in runtime_result.retrieval.chunks:
        source_ref = str(chunk.source_ref or "").strip()
        if source_ref:
            evidence_refs.append(source_ref)

    evidence_refs = list(dict.fromkeys(evidence_refs))
    status = "completed"
    if failed_steps and executed_steps:
        status = "partial"
    elif failed_steps and not executed_steps:
        status = "failed"

    task.plan_json = {
        "goal": task.goal,
        "risk_level": risk_level,
        "requires_approval": approval_required,
        "steps": plan_steps,
        "context_refs": [str(chunk.source_ref or "") for chunk in runtime_result.retrieval.chunks if str(chunk.source_ref or "").strip()],
        "runtime_graph": runtime_result.plan.to_dict(),
    }
    task.result_json = {
        "task_id": task.task_id,
        "goal": task.goal,
        "status": status,
        "risk_level": risk_level,
        "requires_approval": approval_required,
        "reply": runtime_result.reply,
        "plan_summary": {
            "step_count": len(plan_steps),
            "tools": planned_tools,
        },
        "executed_steps": executed_steps,
        "failed_steps": failed_steps,
        "evidence_refs": evidence_refs,
        "evaluation": runtime_result.evaluation.to_dict(),
        "runtime_response": runtime_result.to_dict(),
    }
    task.risk_level = risk_level
    task.requires_approval = "true" if approval_required else "false"
    task.status = status
    task.error_detail = None


def _planned_tools_from_response(runtime_result: RuntimeResponse) -> list[str]:
    tools: list[str] = []
    for node in runtime_result.plan.nodes:
        if node.kind != "execute_tools":
            continue
        node_tools = node.payload.get("tools")
        if isinstance(node_tools, list):
            for item in node_tools:
                tool_name = str(item or "").strip()
                if tool_name:
                    tools.append(tool_name)
    if tools:
        return list(dict.fromkeys(tools))
    return [item.tool_name for item in runtime_result.tool_results if str(item.tool_name or "").strip()]


def _extract_evidence_ref(output: dict[str, Any]) -> str | None:
    if not isinstance(output, dict):
        return None
    for key in ("artifact_uri", "file_id", "source_ref", "task_id"):
        value = str(output.get(key) or "").strip()
        if value:
            return value
    return None
