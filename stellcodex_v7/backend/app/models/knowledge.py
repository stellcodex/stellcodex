from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class KnowledgeRecord(Base):
    __tablename__ = "knowledge_records"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "source_ref",
            "hash_sha256",
            "index_version",
            name="ux_knowledge_records_source_hash",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_id = Column(String(64), nullable=False, unique=True, index=True)
    tenant_id = Column(BigInteger, nullable=False, index=True)
    project_id = Column(String(128), nullable=True, index=True)
    file_id = Column(String(40), nullable=True, index=True)
    source_type = Column(String(64), nullable=False, index=True)
    source_subtype = Column(String(64), nullable=False)
    source_ref = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    summary = Column(Text, nullable=False)
    text = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=False, default=dict)
    tags_json = Column(JSON, nullable=False, default=list)
    security_class = Column(String(32), nullable=False, default="internal")
    hash_sha256 = Column(String(64), nullable=False)
    index_version = Column(String(32), nullable=False, default="v1")
    embedding_status = Column(String(24), nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class KnowledgeIndexJob(Base):
    __tablename__ = "knowledge_index_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(String(64), nullable=True, index=True)
    event_type = Column(String(64), nullable=True, index=True)
    tenant_id = Column(BigInteger, nullable=True, index=True)
    project_id = Column(String(128), nullable=True, index=True)
    file_id = Column(String(40), nullable=True, index=True)
    source_ref = Column(Text, nullable=True)
    status = Column(String(24), nullable=False, default="pending", index=True)
    failure_code = Column(String(64), nullable=True, index=True)
    error_detail = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    payload_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
