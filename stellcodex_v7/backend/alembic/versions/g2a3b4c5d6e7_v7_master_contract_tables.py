"""ensure v7 master-contract tables exist

Revision ID: g2a3b4c5d6e7
Revises: f1c2d3e4f5a6
Create Date: 2026-03-07 21:20:00.000000
"""

from __future__ import annotations

from alembic import op


revision = "g2a3b4c5d6e7"
down_revision = "f1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS tenants (
            id BIGSERIAL PRIMARY KEY,
            code VARCHAR(128) NOT NULL UNIQUE,
            name VARCHAR(255) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS memberships (
            id BIGSERIAL PRIMARY KEY,
            tenant_id BIGINT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role VARCHAR(64) NOT NULL DEFAULT 'member',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (tenant_id, user_id)
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS plans (
            id BIGSERIAL PRIMARY KEY,
            code VARCHAR(128) NOT NULL UNIQUE,
            name VARCHAR(255) NOT NULL,
            limits_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS subscriptions (
            id BIGSERIAL PRIMARY KEY,
            tenant_id BIGINT NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
            plan_id BIGINT NOT NULL REFERENCES plans(id) ON DELETE RESTRICT,
            status VARCHAR(64) NOT NULL DEFAULT 'active',
            started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            ends_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS files (
            id VARCHAR(40) PRIMARY KEY,
            file_id VARCHAR(40) NOT NULL UNIQUE,
            uploaded_file_id VARCHAR(40) UNIQUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_files_file_id ON files (file_id)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_files_uploaded_file_id ON files (uploaded_file_id)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS file_versions (
            id BIGSERIAL PRIMARY KEY,
            file_id VARCHAR(40) NOT NULL REFERENCES files(id) ON DELETE CASCADE,
            version_no INTEGER NOT NULL,
            uploaded_file_id VARCHAR(40),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (file_id, version_no)
        )
        """
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ux_file_versions_file_ver ON file_versions (file_id, version_no)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS job_logs (
            id BIGSERIAL PRIMARY KEY,
            job_id TEXT,
            file_id VARCHAR(40),
            stage VARCHAR(64),
            message TEXT NOT NULL,
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS job_logs")
    op.execute("DROP TABLE IF EXISTS file_versions")
    op.execute("DROP TABLE IF EXISTS files")
    op.execute("DROP TABLE IF EXISTS subscriptions")
    op.execute("DROP TABLE IF EXISTS plans")
    op.execute("DROP TABLE IF EXISTS memberships")
    op.execute("DROP TABLE IF EXISTS tenants")
