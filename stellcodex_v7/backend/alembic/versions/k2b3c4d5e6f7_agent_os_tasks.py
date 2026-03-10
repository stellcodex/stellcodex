"""agent os tasks table

Revision ID: k2b3c4d5e6f7
Revises: j1a2b3c4d5e6
Create Date: 2026-03-08 16:00:00.000000
"""
from __future__ import annotations
from alembic import op


revision = "k2b3c4d5e6f7"
down_revision = "j1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS agent_tasks (
            id UUID PRIMARY KEY,
            task_id VARCHAR(64) NOT NULL UNIQUE,
            tenant_id BIGINT NOT NULL,
            project_id VARCHAR(128),
            trace_id VARCHAR(64) NOT NULL,
            goal TEXT NOT NULL,
            status VARCHAR(24) NOT NULL DEFAULT 'pending',
            risk_level VARCHAR(16) NOT NULL DEFAULT 'low',
            requires_approval VARCHAR(8) NOT NULL DEFAULT 'false',
            plan_json JSONB,
            result_json JSONB,
            error_detail TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_agent_tasks_task_id ON agent_tasks (task_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_agent_tasks_tenant_id ON agent_tasks (tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_agent_tasks_status ON agent_tasks (status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_agent_tasks_project_id ON agent_tasks (project_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS agent_tasks")
