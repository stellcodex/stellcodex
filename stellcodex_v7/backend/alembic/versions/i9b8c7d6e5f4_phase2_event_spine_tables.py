"""phase2 event spine + cache + idempotency + projections

Revision ID: i9b8c7d6e5f4
Revises: h4d5e6f7a8b9
Create Date: 2026-03-08 08:00:00.000000
"""

from __future__ import annotations

from alembic import op


revision = "i9b8c7d6e5f4"
down_revision = "h4d5e6f7a8b9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS artifact_manifest (
            id BIGSERIAL PRIMARY KEY,
            file_id VARCHAR(40) NOT NULL REFERENCES uploaded_files(file_id) ON DELETE CASCADE,
            version_no INTEGER NOT NULL,
            stage VARCHAR(32) NOT NULL,
            input_hash VARCHAR(64) NOT NULL,
            artifact_hash VARCHAR(64),
            artifact_uri TEXT,
            artifact_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            status VARCHAR(24) NOT NULL DEFAULT 'ready',
            cache_hit_count INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ux_artifact_manifest_file_version_stage UNIQUE (file_id, version_no, stage)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_artifact_manifest_file_id ON artifact_manifest (file_id)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS processed_event_ids (
            id UUID PRIMARY KEY,
            event_id VARCHAR(64) NOT NULL,
            event_type VARCHAR(64) NOT NULL,
            consumer VARCHAR(128) NOT NULL,
            file_id VARCHAR(40),
            version_no INTEGER,
            trace_id VARCHAR(64),
            payload JSONB NOT NULL DEFAULT '{}'::jsonb,
            processed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ux_processed_event_consumer UNIQUE (event_id, consumer)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_processed_event_ids_file_id ON processed_event_ids (file_id)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS stage_locks (
            id UUID PRIMARY KEY,
            file_id VARCHAR(40) NOT NULL,
            version_no INTEGER NOT NULL,
            stage VARCHAR(32) NOT NULL,
            lock_token VARCHAR(64) NOT NULL,
            locked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            expires_at TIMESTAMPTZ NOT NULL,
            CONSTRAINT ux_stage_lock_file_version_stage UNIQUE (file_id, version_no, stage)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_stage_locks_file_id ON stage_locks (file_id)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS dlq_records (
            id UUID PRIMARY KEY,
            event_id VARCHAR(64),
            event_type VARCHAR(64),
            file_id VARCHAR(40),
            version_no INTEGER,
            stage VARCHAR(32),
            failure_code VARCHAR(64) NOT NULL,
            error_detail TEXT,
            retry_count INTEGER NOT NULL DEFAULT 0,
            payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_dlq_records_event_id ON dlq_records (event_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_dlq_records_file_id ON dlq_records (file_id)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS file_read_projections (
            file_id VARCHAR(40) PRIMARY KEY REFERENCES uploaded_files(file_id) ON DELETE CASCADE,
            latest_state VARCHAR(32) NOT NULL DEFAULT 'queued',
            stage_progress INTEGER NOT NULL DEFAULT 0,
            decision_summary TEXT,
            risk_summary TEXT,
            approval_status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
            status VARCHAR(24) NOT NULL DEFAULT 'queued',
            kind VARCHAR(16),
            mode VARCHAR(32),
            part_count INTEGER,
            error_code VARCHAR(64),
            timestamps JSONB NOT NULL DEFAULT '{}'::jsonb,
            payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS file_read_projections")
    op.execute("DROP TABLE IF EXISTS dlq_records")
    op.execute("DROP TABLE IF EXISTS stage_locks")
    op.execute("DROP TABLE IF EXISTS processed_event_ids")
    op.execute("DROP TABLE IF EXISTS artifact_manifest")
