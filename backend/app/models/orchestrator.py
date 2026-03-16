import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.base import Base


class OrchestratorSession(Base):
    __tablename__ = "orchestrator_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(String(40), nullable=False, unique=True, index=True)
    state = Column(String(8), nullable=False, default="S0")
    state_code = Column(String(8), nullable=False, default="S0")
    state_label = Column(String(64), nullable=False, default="uploaded")
    status_gate = Column(String(32), nullable=False, default="PASS")
    approval_required = Column(Boolean, nullable=False, default=False)
    rule_version = Column(String(32), nullable=False, default="v0.0")
    mode = Column(String(32), nullable=False, default="visual_only")
    confidence = Column(Float, nullable=False, default=0.0)
    risk_flags = Column(JSONB, nullable=False, default=list)
    decision_json = Column(JSONB, nullable=False, default=dict)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, onupdate=datetime.utcnow)
