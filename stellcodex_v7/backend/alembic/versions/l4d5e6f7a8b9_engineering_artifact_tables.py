"""engineering artifact persistence tables

Revision ID: l4d5e6f7a8b9
Revises: k2b3c4d5e6f7
Create Date: 2026-03-10 22:05:00.000000
"""

from __future__ import annotations

from alembic import op


revision = "l4d5e6f7a8b9"
down_revision = "k2b3c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS cost_estimates (
            id UUID PRIMARY KEY,
            tenant_id BIGINT NOT NULL,
            file_id VARCHAR(40) NOT NULL REFERENCES uploaded_files(file_id) ON DELETE CASCADE,
            session_id VARCHAR(64),
            geometry_hash VARCHAR(64) NOT NULL,
            recommended_process VARCHAR(64) NOT NULL DEFAULT 'unknown',
            currency VARCHAR(16) NOT NULL DEFAULT 'EUR',
            estimated_unit_cost DOUBLE PRECISION,
            estimated_batch_cost DOUBLE PRECISION,
            estimate_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            estimate_hash VARCHAR(64) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ux_cost_estimates_tenant_file_hash UNIQUE (tenant_id, file_id, geometry_hash)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_cost_estimates_tenant_id ON cost_estimates (tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_cost_estimates_file_id ON cost_estimates (file_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_cost_estimates_session_id ON cost_estimates (session_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_cost_estimates_geometry_hash ON cost_estimates (geometry_hash)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS manufacturing_plans (
            id UUID PRIMARY KEY,
            tenant_id BIGINT NOT NULL,
            file_id VARCHAR(40) NOT NULL REFERENCES uploaded_files(file_id) ON DELETE CASCADE,
            session_id VARCHAR(64),
            geometry_hash VARCHAR(64) NOT NULL,
            recommended_process VARCHAR(64) NOT NULL DEFAULT 'unknown',
            setup_count BIGINT,
            estimated_cycle_time_minutes DOUBLE PRECISION,
            estimated_batch_time_minutes DOUBLE PRECISION,
            plan_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            plan_hash VARCHAR(64) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ux_manufacturing_plans_tenant_file_hash UNIQUE (tenant_id, file_id, geometry_hash)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_manufacturing_plans_tenant_id ON manufacturing_plans (tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_manufacturing_plans_file_id ON manufacturing_plans (file_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_manufacturing_plans_session_id ON manufacturing_plans (session_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_manufacturing_plans_geometry_hash ON manufacturing_plans (geometry_hash)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS engineering_reports (
            id UUID PRIMARY KEY,
            tenant_id BIGINT NOT NULL,
            file_id VARCHAR(40) NOT NULL REFERENCES uploaded_files(file_id) ON DELETE CASCADE,
            session_id VARCHAR(64),
            geometry_hash VARCHAR(64) NOT NULL,
            capability_status VARCHAR(32) NOT NULL DEFAULT 'degraded',
            report_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            report_hash VARCHAR(64) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ux_engineering_reports_tenant_file_hash UNIQUE (tenant_id, file_id, geometry_hash)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_engineering_reports_tenant_id ON engineering_reports (tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_engineering_reports_file_id ON engineering_reports (file_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_engineering_reports_session_id ON engineering_reports (session_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_engineering_reports_geometry_hash ON engineering_reports (geometry_hash)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS engineering_reports")
    op.execute("DROP TABLE IF EXISTS manufacturing_plans")
    op.execute("DROP TABLE IF EXISTS cost_estimates")
