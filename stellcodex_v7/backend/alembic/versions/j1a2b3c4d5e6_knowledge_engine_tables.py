"""knowledge engine tables

Revision ID: j1a2b3c4d5e6
Revises: i9b8c7d6e5f4
Create Date: 2026-03-08 12:15:00.000000
"""

from __future__ import annotations

from alembic import op


revision = "j1a2b3c4d5e6"
down_revision = "i9b8c7d6e5f4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_records (
            id UUID PRIMARY KEY,
            record_id VARCHAR(64) NOT NULL UNIQUE,
            tenant_id BIGINT NOT NULL,
            project_id VARCHAR(128),
            file_id VARCHAR(40),
            source_type VARCHAR(64) NOT NULL,
            source_subtype VARCHAR(64) NOT NULL,
            source_ref TEXT NOT NULL,
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            text TEXT NOT NULL,
            metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            tags_json JSONB NOT NULL DEFAULT '[]'::jsonb,
            security_class VARCHAR(32) NOT NULL DEFAULT 'internal',
            hash_sha256 VARCHAR(64) NOT NULL,
            index_version VARCHAR(32) NOT NULL DEFAULT 'v1',
            embedding_status VARCHAR(24) NOT NULL DEFAULT 'pending',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT ux_knowledge_records_source_hash UNIQUE (tenant_id, source_ref, hash_sha256, index_version)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_knowledge_records_tenant_id ON knowledge_records (tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_knowledge_records_project_id ON knowledge_records (project_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_knowledge_records_file_id ON knowledge_records (file_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_knowledge_records_source_type ON knowledge_records (source_type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_knowledge_records_record_id ON knowledge_records (record_id)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS knowledge_index_jobs (
            id UUID PRIMARY KEY,
            event_id VARCHAR(64),
            event_type VARCHAR(64),
            tenant_id BIGINT,
            project_id VARCHAR(128),
            file_id VARCHAR(40),
            source_ref TEXT,
            status VARCHAR(24) NOT NULL DEFAULT 'pending',
            failure_code VARCHAR(64),
            error_detail TEXT,
            retry_count INTEGER NOT NULL DEFAULT 0,
            payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_knowledge_index_jobs_event_id ON knowledge_index_jobs (event_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_knowledge_index_jobs_event_type ON knowledge_index_jobs (event_type)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_knowledge_index_jobs_tenant_id ON knowledge_index_jobs (tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_knowledge_index_jobs_project_id ON knowledge_index_jobs (project_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_knowledge_index_jobs_file_id ON knowledge_index_jobs (file_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_knowledge_index_jobs_status ON knowledge_index_jobs (status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_knowledge_index_jobs_failure_code ON knowledge_index_jobs (failure_code)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS knowledge_index_jobs")
    op.execute("DROP TABLE IF EXISTS knowledge_records")
