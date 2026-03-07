"""expand upload file_id length for scx prefix

Revision ID: d2b1b7f2a1cd
Revises: 0e2184fecd30
Create Date: 2026-02-10 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d2b1b7f2a1cd"
down_revision = "0e2184fecd30"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "uploaded_files",
        "file_id",
        existing_type=sa.String(length=36),
        type_=sa.String(length=40),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "uploaded_files",
        "file_id",
        existing_type=sa.String(length=40),
        type_=sa.String(length=36),
        existing_nullable=False,
    )
