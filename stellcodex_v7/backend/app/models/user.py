import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(Text, nullable=True, unique=True)
    password_hash = Column(Text, nullable=True)
    role = Column(String(32), nullable=False, default="user")
    is_suspended = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    jti = Column(String(64), primary_key=True)
    revoked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    reason = Column(Text, nullable=True)
