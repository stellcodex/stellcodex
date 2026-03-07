import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(64), nullable=False)
    actor_user_id = Column(UUID(as_uuid=True), nullable=True)
    actor_anon_sub = Column(Text, nullable=True)
    file_id = Column(Text, nullable=True)
    data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
