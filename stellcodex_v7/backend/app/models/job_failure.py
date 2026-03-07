import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class JobFailure(Base):
    __tablename__ = "job_failures"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(Text, nullable=True)
    file_id = Column(Text, nullable=True)
    stage = Column(String(32), nullable=False)
    error_class = Column(String(128), nullable=False)
    message = Column(Text, nullable=False)
    traceback = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
