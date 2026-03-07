from __future__ import annotations

from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class OrchestratorSession(Base):
    __tablename__ = "orchestrator_sessions"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    file_id: Mapped[str] = mapped_column(
        String(40),
        ForeignKey("uploaded_files.file_id"),
        unique=True,
        nullable=False,
        index=True,
    )
    state_code: Mapped[str] = mapped_column(String(8), nullable=False, default="S0")
    state_label: Mapped[str] = mapped_column(String(64), nullable=False, default="uploaded")
    status_gate: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    approval_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    risk_flags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    decision_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


class RuleConfig(Base):
    __tablename__ = "rule_configs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    value_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
