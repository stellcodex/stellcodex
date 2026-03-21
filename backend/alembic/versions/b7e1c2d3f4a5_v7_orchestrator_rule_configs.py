"""v7 orchestrator sessions and rule configs

Revision ID: b7e1c2d3f4a5
Revises: a1b2c3d4e5f6
Create Date: 2026-03-14 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "b7e1c2d3f4a5"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "orchestrator_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("file_id", sa.String(length=40), nullable=False),
        sa.Column("state", sa.Text(), nullable=False),
        sa.Column("decision_json", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
        sa.Column("rule_version", sa.Text(), nullable=False, server_default="v0.0"),
        sa.Column("mode", sa.Text(), nullable=False, server_default="visual_only"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_orchestrator_sessions_file_id", "orchestrator_sessions", ["file_id"])
    op.create_index("idx_orchestrator_sessions_state", "orchestrator_sessions", ["state"])

    op.create_table(
        "rule_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scope", sa.Text(), nullable=False, server_default="global"),
        sa.Column("scope_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("value_json", sa.JSON(), nullable=False),
        sa.Column("version", sa.Text(), nullable=False, server_default="v0.0"),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )
    op.create_unique_constraint("uq_rule_config_scope_key", "rule_configs", ["scope", "scope_id", "key"])


def downgrade() -> None:
    op.drop_constraint("uq_rule_config_scope_key", "rule_configs", type_="unique")
    op.drop_table("rule_configs")
    op.drop_index("idx_orchestrator_sessions_state", table_name="orchestrator_sessions")
    op.drop_index("idx_orchestrator_sessions_file_id", table_name="orchestrator_sessions")
    op.drop_table("orchestrator_sessions")
