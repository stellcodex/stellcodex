import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class Share(Base):
    __tablename__ = "shares"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(Text, nullable=False, index=True)
    created_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    token = Column(String(128), nullable=False, unique=True, index=True)
    permission = Column(String(16), nullable=False, default="view")
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
