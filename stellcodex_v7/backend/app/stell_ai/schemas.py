"""Pydantic schemas for Agent OS API contracts."""
from __future__ import annotations

from typing import Any
from pydantic import BaseModel, Field


# ── Event Ingest ─────────────────────────────────────────────────────────────

class EventIngestIn(BaseModel):
    event_type: str
    source: str
    subject: str
    tenant_id: str | None = None
    project_id: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    trace_id: str | None = None


class EventIngestOut(BaseModel):
    event_id: str
    trace_id: str
    status: str
    duplicate: bool


# ── Task Submit ───────────────────────────────────────────────────────────────

class TaskSubmitIn(BaseModel):
    goal: str
    project_id: str | None = None
    file_ids: list[str] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)
    execute: bool = True


class PlanStep(BaseModel):
    step_id: str
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    requires_approval: bool = False
    rollback_note: str = ""


class TaskPlan(BaseModel):
    goal: str
    risk_level: str
    requires_approval: bool
    steps: list[PlanStep]
    context_refs: list[str] = Field(default_factory=list)


class StepResult(BaseModel):
    step_id: str
    tool: str
    success: bool
    output: Any = None
    error: str | None = None
    evidence_ref: str | None = None


class TaskResult(BaseModel):
    task_id: str
    goal: str
    status: str
    risk_level: str
    plan: TaskPlan
    executed_steps: list[StepResult]
    failed_steps: list[StepResult]
    evidence_refs: list[str]
    report_markdown: str
    report_json: dict[str, Any]


class TaskSubmitOut(BaseModel):
    task_id: str
    trace_id: str
    status: str
    plan: TaskPlan | None = None
    result: TaskResult | None = None


# ── Task Status ───────────────────────────────────────────────────────────────

class TaskStatusOut(BaseModel):
    task_id: str
    status: str
    goal: str
    risk_level: str
    tenant_id: str
    trace_id: str
    plan: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    error_detail: str | None = None
    created_at: str
    updated_at: str
