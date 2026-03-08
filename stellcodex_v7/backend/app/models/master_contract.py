from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(128), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Membership(Base):
    __tablename__ = "memberships"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, ForeignKey("tenants.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    role = Column(String(64), nullable=False, default="member")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Plan(Base):
    __tablename__ = "plans"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    code = Column(String(128), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    limits_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    tenant_id = Column(BigInteger, ForeignKey("tenants.id"), nullable=False)
    plan_id = Column(BigInteger, ForeignKey("plans.id"), nullable=False)
    status = Column(String(64), nullable=False, default="active")
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ends_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class FileRegistry(Base):
    __tablename__ = "files"

    id = Column(String(40), primary_key=True)
    file_id = Column(String(40), nullable=False, unique=True)
    uploaded_file_id = Column(String(40), nullable=True, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class FileVersion(Base):
    __tablename__ = "file_versions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    file_id = Column(String(40), ForeignKey("files.id"), nullable=False)
    version_no = Column(Integer, nullable=False)
    uploaded_file_id = Column(String(40), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class JobLog(Base):
    __tablename__ = "job_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    job_id = Column(Text, nullable=True)
    file_id = Column(String(40), nullable=True)
    stage = Column(String(64), nullable=True)
    message = Column(Text, nullable=False)
    payload = Column(JSON, nullable=False, default=dict)
    immutable = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
