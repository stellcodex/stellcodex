"""AgentTask — DB model for Agent OS task tracking."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(String(64), nullable=False, unique=True, index=True)
    tenant_id = Column(BigInteger, nullable=False, index=True)
    project_id = Column(String(128), nullable=True, index=True)
    trace_id = Column(String(64), nullable=False)
    goal = Column(Text, nullable=False)
    status = Column(String(24), nullable=False, default="pending", index=True)
    risk_level = Column(String(16), nullable=False, default="low")
    requires_approval = Column(String(8), nullable=False, default="false")
    plan_json = Column(JSON, nullable=True)
    result_json = Column(JSON, nullable=True)
    error_detail = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
