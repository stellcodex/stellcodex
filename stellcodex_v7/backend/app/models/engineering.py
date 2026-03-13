"""Schema-backed engineering artifact models.

These tables persist the deterministic engineering pipeline outputs. Update this
file and the matching Alembic revision together when adding new artifact types.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class GeometryMetric(Base):
    __tablename__ = "geometry_metrics"
    __table_args__ = (
        UniqueConstraint("tenant_id", "file_id", "geometry_hash", name="ux_geometry_metrics_tenant_file_hash"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(BigInteger, nullable=False, index=True)
    file_id = Column(String(40), ForeignKey("uploaded_files.file_id", ondelete="CASCADE"), nullable=False, index=True)
    geometry_hash = Column(String(64), nullable=False, index=True)
    mode = Column(String(32), nullable=False)
    units = Column(String(16), nullable=False, default="mm")
    volume = Column(Float, nullable=True)
    surface_area = Column(Float, nullable=True)
    bbox_json = Column(JSON, nullable=False, default=dict)
    triangle_count = Column(BigInteger, nullable=True)
    part_count = Column(BigInteger, nullable=True)
    wall_thickness_stats = Column(JSON, nullable=False, default=dict)
    mass_estimate = Column(Float, nullable=True)
    metadata_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class FeatureMap(Base):
    __tablename__ = "feature_maps"
    __table_args__ = (
        UniqueConstraint("tenant_id", "file_id", "geometry_hash", name="ux_feature_maps_tenant_file_hash"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(BigInteger, nullable=False, index=True)
    file_id = Column(String(40), ForeignKey("uploaded_files.file_id", ondelete="CASCADE"), nullable=False, index=True)
    geometry_hash = Column(String(64), nullable=False, index=True)
    feature_map_json = Column(JSON, nullable=False, default=dict)
    extractor_version = Column(String(32), nullable=False, default="engineering_features.v1")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DesignIntentRecord(Base):
    __tablename__ = "design_intent"
    __table_args__ = (
        UniqueConstraint("tenant_id", "file_id", "geometry_hash", name="ux_design_intent_tenant_file_hash"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(BigInteger, nullable=False, index=True)
    file_id = Column(String(40), ForeignKey("uploaded_files.file_id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(64), nullable=True, index=True)
    geometry_hash = Column(String(64), nullable=False, index=True)
    intent_json = Column(JSON, nullable=False, default=dict)
    intent_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DfmReportRecord(Base):
    __tablename__ = "dfm_reports"
    __table_args__ = (
        UniqueConstraint("tenant_id", "file_id", "geometry_hash", "rule_version", name="ux_dfm_reports_tenant_file_hash_rule"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(BigInteger, nullable=False, index=True)
    file_id = Column(String(40), ForeignKey("uploaded_files.file_id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(64), nullable=True, index=True)
    geometry_hash = Column(String(64), nullable=False, index=True)
    mode = Column(String(32), nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)
    rule_version = Column(String(32), nullable=False)
    report_json = Column(JSON, nullable=False, default=dict)
    report_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CostEstimateRecord(Base):
    __tablename__ = "cost_estimates"
    __table_args__ = (
        UniqueConstraint("tenant_id", "file_id", "geometry_hash", name="ux_cost_estimates_tenant_file_hash"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(BigInteger, nullable=False, index=True)
    file_id = Column(String(40), ForeignKey("uploaded_files.file_id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(64), nullable=True, index=True)
    geometry_hash = Column(String(64), nullable=False, index=True)
    recommended_process = Column(String(64), nullable=False, default="unknown")
    currency = Column(String(16), nullable=False, default="EUR")
    estimated_unit_cost = Column(Float, nullable=True)
    estimated_batch_cost = Column(Float, nullable=True)
    estimate_json = Column(JSON, nullable=False, default=dict)
    estimate_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class CostOptimizationRecord(Base):
    __tablename__ = "cost_optimizations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "file_id", "geometry_hash", name="ux_cost_optimizations_tenant_file_hash"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(BigInteger, nullable=False, index=True)
    file_id = Column(String(40), ForeignKey("uploaded_files.file_id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(64), nullable=True, index=True)
    geometry_hash = Column(String(64), nullable=False, index=True)
    optimization_json = Column(JSON, nullable=False, default=dict)
    optimization_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ManufacturingPlanRecord(Base):
    __tablename__ = "manufacturing_plans"
    __table_args__ = (
        UniqueConstraint("tenant_id", "file_id", "geometry_hash", name="ux_manufacturing_plans_tenant_file_hash"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(BigInteger, nullable=False, index=True)
    file_id = Column(String(40), ForeignKey("uploaded_files.file_id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(64), nullable=True, index=True)
    geometry_hash = Column(String(64), nullable=False, index=True)
    recommended_process = Column(String(64), nullable=False, default="unknown")
    setup_count = Column(BigInteger, nullable=True)
    estimated_cycle_time_minutes = Column(Float, nullable=True)
    estimated_batch_time_minutes = Column(Float, nullable=True)
    plan_json = Column(JSON, nullable=False, default=dict)
    plan_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ProcessSimulationRecord(Base):
    __tablename__ = "process_simulations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "file_id", "geometry_hash", name="ux_process_simulations_tenant_file_hash"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(BigInteger, nullable=False, index=True)
    file_id = Column(String(40), ForeignKey("uploaded_files.file_id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(64), nullable=True, index=True)
    geometry_hash = Column(String(64), nullable=False, index=True)
    simulation_json = Column(JSON, nullable=False, default=dict)
    simulation_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class EngineeringReportRecord(Base):
    __tablename__ = "engineering_reports"
    __table_args__ = (
        UniqueConstraint("tenant_id", "file_id", "geometry_hash", name="ux_engineering_reports_tenant_file_hash"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(BigInteger, nullable=False, index=True)
    file_id = Column(String(40), ForeignKey("uploaded_files.file_id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(64), nullable=True, index=True)
    geometry_hash = Column(String(64), nullable=False, index=True)
    capability_status = Column(String(32), nullable=False, default="degraded")
    report_json = Column(JSON, nullable=False, default=dict)
    report_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DesignOptimizationRecord(Base):
    __tablename__ = "design_optimizations"
    __table_args__ = (
        UniqueConstraint("tenant_id", "file_id", "geometry_hash", name="ux_design_optimizations_tenant_file_hash"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(BigInteger, nullable=False, index=True)
    file_id = Column(String(40), ForeignKey("uploaded_files.file_id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(64), nullable=True, index=True)
    geometry_hash = Column(String(64), nullable=False, index=True)
    optimization_json = Column(JSON, nullable=False, default=dict)
    optimization_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class ArtifactCacheEntry(Base):
    __tablename__ = "artifact_cache"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "file_id",
            "geometry_hash",
            "analysis_type",
            name="ux_artifact_cache_tenant_file_hash_type",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(BigInteger, nullable=False, index=True)
    file_id = Column(String(40), ForeignKey("uploaded_files.file_id", ondelete="CASCADE"), nullable=False, index=True)
    geometry_hash = Column(String(64), nullable=False, index=True)
    analysis_type = Column(String(64), nullable=False, index=True)
    artifact_hash = Column(String(64), nullable=False)
    artifact_uri_ref = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(BigInteger, nullable=False, index=True)
    file_id = Column(String(40), ForeignKey("uploaded_files.file_id", ondelete="CASCADE"), nullable=False, index=True)
    session_id = Column(String(64), nullable=True, index=True)
    run_type = Column(String(64), nullable=False)
    status = Column(String(32), nullable=False, default="running")
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    metrics_json = Column(JSON, nullable=False, default=dict)
    error_code = Column(String(64), nullable=True)


class WorkerNode(Base):
    __tablename__ = "worker_nodes"

    worker_id = Column(String(128), primary_key=True)
    provider = Column(String(64), nullable=False)
    region = Column(String(64), nullable=True)
    cpu = Column(BigInteger, nullable=True)
    ram_mb = Column(BigInteger, nullable=True)
    gpu_enabled = Column(Boolean, nullable=False, default=False)
    capabilities_json = Column(JSON, nullable=False, default=dict)
    status = Column(String(32), nullable=False, default="online", index=True)
    version = Column(String(64), nullable=True)
    last_heartbeat = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    metadata_json = Column(JSON, nullable=False, default=dict)
