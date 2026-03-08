from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class ArtifactManifest(Base):
    __tablename__ = "artifact_manifest"
    __table_args__ = (
        UniqueConstraint("file_id", "version_no", "stage", name="ux_artifact_manifest_file_version_stage"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    file_id = Column(String(40), ForeignKey("uploaded_files.file_id", ondelete="CASCADE"), nullable=False, index=True)
    version_no = Column(Integer, nullable=False, default=1)
    stage = Column(String(32), nullable=False)
    input_hash = Column(String(64), nullable=False)
    artifact_hash = Column(String(64), nullable=True)
    artifact_uri = Column(Text, nullable=True)
    artifact_payload = Column(JSON, nullable=False, default=dict)
    status = Column(String(24), nullable=False, default="ready")
    cache_hit_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ProcessedEventId(Base):
    __tablename__ = "processed_event_ids"
    __table_args__ = (
        UniqueConstraint("event_id", "consumer", name="ux_processed_event_consumer"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(String(64), nullable=False)
    event_type = Column(String(64), nullable=False)
    consumer = Column(String(128), nullable=False)
    file_id = Column(String(40), nullable=True, index=True)
    version_no = Column(Integer, nullable=True)
    trace_id = Column(String(64), nullable=True)
    payload = Column(JSON, nullable=False, default=dict)
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class StageLock(Base):
    __tablename__ = "stage_locks"
    __table_args__ = (
        UniqueConstraint("file_id", "version_no", "stage", name="ux_stage_lock_file_version_stage"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_id = Column(String(40), nullable=False, index=True)
    version_no = Column(Integer, nullable=False, default=1)
    stage = Column(String(32), nullable=False)
    lock_token = Column(String(64), nullable=False)
    locked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)


class DlqRecord(Base):
    __tablename__ = "dlq_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_id = Column(String(64), nullable=True, index=True)
    event_type = Column(String(64), nullable=True)
    file_id = Column(String(40), nullable=True, index=True)
    version_no = Column(Integer, nullable=True)
    stage = Column(String(32), nullable=True)
    failure_code = Column(String(64), nullable=False)
    error_detail = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    payload_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class FileReadProjection(Base):
    __tablename__ = "file_read_projections"

    file_id = Column(String(40), ForeignKey("uploaded_files.file_id", ondelete="CASCADE"), primary_key=True)
    latest_state = Column(String(32), nullable=False, default="queued")
    stage_progress = Column(Integer, nullable=False, default=0)
    decision_summary = Column(Text, nullable=True)
    risk_summary = Column(Text, nullable=True)
    approval_status = Column(String(32), nullable=False, default="PENDING")
    status = Column(String(24), nullable=False, default="queued")
    kind = Column(String(16), nullable=True)
    mode = Column(String(32), nullable=True)
    part_count = Column(Integer, nullable=True)
    error_code = Column(String(64), nullable=True)
    timestamps = Column(JSON, nullable=False, default=dict)
    payload_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
