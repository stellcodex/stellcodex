import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class LibraryItem(Base):
    __tablename__ = "library_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_key = Column(Text, nullable=False, index=True)
    owner_user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    file_id = Column(Text, nullable=False, index=True)
    visibility = Column(String(16), nullable=False, default="private")  # private | unlisted | public
    slug = Column(String(180), nullable=False, unique=True, index=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=False, default=list)
    cover_thumb = Column(Text, nullable=True)
    share_token = Column(String(128), nullable=True)
    stats = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

