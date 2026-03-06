"""v7 orchestrator sessions + rule configs + decision_json

Revision ID: c9a5f0f3e1b2
Revises: a1b2c3d4e5f6
Create Date: 2026-03-05 17:10:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "c9a5f0f3e1b2"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS decision_json JSONB")
    op.execute("UPDATE uploaded_files SET decision_json = '{}'::jsonb WHERE decision_json IS NULL")
    op.execute("ALTER TABLE uploaded_files ALTER COLUMN decision_json SET NOT NULL")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS orchestrator_sessions (
            id UUID PRIMARY KEY,
            file_id VARCHAR(40) NOT NULL UNIQUE,
            state_code VARCHAR(8) NOT NULL DEFAULT 'S0',
            state_label VARCHAR(64) NOT NULL DEFAULT 'uploaded',
            status_gate VARCHAR(32) NOT NULL DEFAULT 'PENDING',
            approval_required BOOLEAN NOT NULL DEFAULT false,
            risk_flags JSONB NOT NULL DEFAULT '[]'::jsonb,
            decision_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            notes TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT fk_orchestrator_sessions_file_id
              FOREIGN KEY (file_id) REFERENCES uploaded_files(file_id)
        )
        """
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_orchestrator_sessions_file_id ON orchestrator_sessions (file_id)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS rule_configs (
            id UUID PRIMARY KEY,
            key VARCHAR(128) NOT NULL UNIQUE,
            value_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            enabled BOOLEAN NOT NULL DEFAULT true,
            description TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_rule_configs_key ON rule_configs (key)")

    op.execute(
        """
        INSERT INTO rule_configs (id, key, value_json, enabled, description)
        VALUES
          ('5e6b7c20-1324-4a12-9e45-a9ccda100001'::uuid, 'draft_min_deg', '{"value": 1.0}'::jsonb, true, 'Minimum draft angle in degrees'),
          ('5e6b7c20-1324-4a12-9e45-a9ccda100002'::uuid, 'wall_mm_min', '{"value": 1.0}'::jsonb, true, 'Minimum wall thickness (mm)'),
          ('5e6b7c20-1324-4a12-9e45-a9ccda100003'::uuid, 'wall_mm_max', '{"value": 3.0}'::jsonb, true, 'Maximum wall thickness (mm)'),
          ('5e6b7c20-1324-4a12-9e45-a9ccda100004'::uuid, 'block_on_unknown_critical', '{"value": true}'::jsonb, true, 'Block auto approval for unknown critical geometry'),
          ('5e6b7c20-1324-4a12-9e45-a9ccda100005'::uuid, 'force_approval_on_visual_only', '{"value": true}'::jsonb, true, 'Visual-only mode requires manual approval'),
          ('5e6b7c20-1324-4a12-9e45-a9ccda100006'::uuid, 'allow_hot_runner', '{"value": false}'::jsonb, true, 'Hot runner is blocked by default')
        ON CONFLICT (key) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_rule_configs_key")
    op.execute("DROP TABLE IF EXISTS rule_configs")

    op.execute("DROP INDEX IF EXISTS ix_orchestrator_sessions_file_id")
    op.execute("DROP TABLE IF EXISTS orchestrator_sessions")

    op.execute("ALTER TABLE uploaded_files DROP COLUMN IF EXISTS decision_json")
