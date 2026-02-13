"""v1 auth/share/failures tables and ownership columns

Revision ID: f4b1a2c3d4e5
Revises: d2b1b7f2a1cd
Create Date: 2026-02-10 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "f4b1a2c3d4e5"
down_revision = "d2b1b7f2a1cd"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.Text(), nullable=True, unique=True),
        sa.Column("role", sa.String(length=32), nullable=False, server_default="user"),
        sa.Column("is_suspended", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "revoked_tokens",
        sa.Column("jti", sa.String(length=64), primary_key=True, nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.Column("reason", sa.Text(), nullable=True),
    )

    op.create_table(
        "shares",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("file_id", sa.Text(), nullable=False, index=True),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("token", sa.String(length=128), nullable=False, unique=True, index=True),
        sa.Column("permission", sa.String(length=16), nullable=False, server_default="view"),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "job_failures",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("job_id", sa.Text(), nullable=True),
        sa.Column("file_id", sa.Text(), nullable=True),
        sa.Column("stage", sa.String(length=32), nullable=False),
        sa.Column("error_class", sa.String(length=128), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("traceback", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("actor_anon_sub", sa.Text(), nullable=True),
        sa.Column("file_id", sa.Text(), nullable=True),
        sa.Column("data", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
    )

    op.add_column("uploaded_files", sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("uploaded_files", sa.Column("owner_anon_sub", sa.Text(), nullable=True))
    op.add_column(
        "uploaded_files",
        sa.Column("is_anonymous", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )
    op.add_column(
        "uploaded_files",
        sa.Column("privacy", sa.String(length=16), nullable=False, server_default="private"),
    )
    op.add_column("uploaded_files", sa.Column("archived_at", sa.DateTime(), nullable=True))

    op.execute("UPDATE uploaded_files SET owner_anon_sub = owner_sub WHERE owner_anon_sub IS NULL")
    op.execute("UPDATE uploaded_files SET is_anonymous = true WHERE is_anonymous IS NULL")
    op.execute("UPDATE uploaded_files SET privacy = 'private' WHERE privacy IS NULL")


def downgrade() -> None:
    op.drop_column("uploaded_files", "archived_at")
    op.drop_column("uploaded_files", "privacy")
    op.drop_column("uploaded_files", "is_anonymous")
    op.drop_column("uploaded_files", "owner_anon_sub")
    op.drop_column("uploaded_files", "owner_user_id")

    op.drop_table("audit_events")
    op.drop_table("job_failures")
    op.drop_table("shares")
    op.drop_table("revoked_tokens")
    op.drop_table("users")
