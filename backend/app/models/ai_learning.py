from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.db.base import Base


class AiCaseLog(Base):
    __tablename__ = "ai_case_logs"

    case_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(BigInteger, nullable=False, index=True)
    file_id = Column(String(40), nullable=False, index=True)
    project_id = Column(String(128), nullable=False, default="default", index=True)
    session_id = Column(String(64), nullable=True, index=True)
    run_type = Column(String(48), nullable=False, default="session_sync", index=True)
    normalized_problem_signature = Column(Text, nullable=False, index=True)
    similarity_index_key = Column(String(255), nullable=False, index=True)
    input_payload = Column(JSONB, nullable=False, default=dict)
    decision_output = Column(JSONB, nullable=False, default=dict)
    execution_trace = Column(JSONB, nullable=False, default=list)
    final_status = Column(String(16), nullable=False, default="blocked", index=True)
    error_trace = Column(JSONB, nullable=True)
    failure_class = Column(String(32), nullable=True, index=True)
    duration_ms = Column(Integer, nullable=False, default=0)
    drive_snapshot_path = Column(Text, nullable=True)
    drive_snapshot_status = Column(String(16), nullable=False, default="disabled")
    drive_snapshot_error = Column(Text, nullable=True)
    retrieved_context_summary = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)


class AiSnapshotJob(Base):
    __tablename__ = "ai_snapshot_jobs"

    snapshot_job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("ai_case_logs.case_id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    tenant_id = Column(BigInteger, nullable=False, index=True)
    idempotency_key = Column(String(128), nullable=False, unique=True, index=True)
    local_snapshot_path = Column(Text, nullable=False)
    drive_target_path = Column(Text, nullable=True)
    upload_status = Column(String(24), nullable=False, default="queued", index=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    last_error = Column(Text, nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True, index=True)
    locked_at = Column(DateTime(timezone=True), nullable=True)
    locked_by = Column(String(128), nullable=True)
    last_rq_job_id = Column(String(64), nullable=True, index=True)
    uploaded_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, onupdate=datetime.utcnow)


class AiEvalResult(Base):
    __tablename__ = "ai_eval_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    case_id = Column(UUID(as_uuid=True), ForeignKey("ai_case_logs.case_id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    tenant_id = Column(BigInteger, nullable=False, index=True)
    normalized_problem_signature = Column(Text, nullable=False, index=True)
    similarity_index_key = Column(String(255), nullable=False, index=True)
    outcome = Column(String(16), nullable=False, index=True)
    decision_taken = Column(JSONB, nullable=False, default=dict)
    evaluation = Column(JSONB, nullable=False, default=dict)
    failure_class = Column(String(32), nullable=True, index=True)
    resolution_seconds = Column(Float, nullable=False, default=0.0)
    success_rate = Column(Float, nullable=False, default=0.0)
    average_resolution_seconds = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)


class SolvedCase(Base):
    __tablename__ = "solved_cases"

    case_id = Column(UUID(as_uuid=True), ForeignKey("ai_case_logs.case_id", ondelete="CASCADE"), primary_key=True)
    tenant_id = Column(BigInteger, nullable=False, index=True)
    file_id = Column(String(40), nullable=False, index=True)
    project_id = Column(String(128), nullable=False, default="default", index=True)
    normalized_problem_signature = Column(Text, nullable=False, index=True)
    similarity_index_key = Column(String(255), nullable=False, index=True)
    decision_taken = Column(JSONB, nullable=False, default=dict)
    outcome = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)


class FailedCase(Base):
    __tablename__ = "failed_cases"

    case_id = Column(UUID(as_uuid=True), ForeignKey("ai_case_logs.case_id", ondelete="CASCADE"), primary_key=True)
    tenant_id = Column(BigInteger, nullable=False, index=True)
    file_id = Column(String(40), nullable=False, index=True)
    project_id = Column(String(128), nullable=False, default="default", index=True)
    normalized_problem_signature = Column(Text, nullable=False, index=True)
    similarity_index_key = Column(String(255), nullable=False, index=True)
    decision_taken = Column(JSONB, nullable=False, default=dict)
    outcome = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)


class BlockedCase(Base):
    __tablename__ = "blocked_cases"

    case_id = Column(UUID(as_uuid=True), ForeignKey("ai_case_logs.case_id", ondelete="CASCADE"), primary_key=True)
    tenant_id = Column(BigInteger, nullable=False, index=True)
    file_id = Column(String(40), nullable=False, index=True)
    project_id = Column(String(128), nullable=False, default="default", index=True)
    normalized_problem_signature = Column(Text, nullable=False, index=True)
    similarity_index_key = Column(String(255), nullable=False, index=True)
    decision_taken = Column(JSONB, nullable=False, default=dict)
    outcome = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)


class RecoveredCase(Base):
    __tablename__ = "recovered_cases"

    case_id = Column(UUID(as_uuid=True), ForeignKey("ai_case_logs.case_id", ondelete="CASCADE"), primary_key=True)
    tenant_id = Column(BigInteger, nullable=False, index=True)
    file_id = Column(String(40), nullable=False, index=True)
    project_id = Column(String(128), nullable=False, default="default", index=True)
    normalized_problem_signature = Column(Text, nullable=False, index=True)
    similarity_index_key = Column(String(255), nullable=False, index=True)
    decision_taken = Column(JSONB, nullable=False, default=dict)
    outcome = Column(JSONB, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)


class AiPatternSignal(Base):
    __tablename__ = "ai_pattern_signals"

    signal_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(BigInteger, nullable=False, index=True)
    signal_type = Column(String(32), nullable=False, index=True)
    normalized_problem_signature = Column(Text, nullable=False, index=True)
    similarity_index_key = Column(String(255), nullable=False, index=True)
    failure_class = Column(String(32), nullable=True, index=True)
    signal_payload = Column(JSONB, nullable=False, default=dict)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, onupdate=datetime.utcnow)
