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
    # Idempotent DDL: this repo may pre-create tables during startup.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY,
            email TEXT UNIQUE,
            role VARCHAR(32) NOT NULL DEFAULT 'user',
            is_suspended BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS revoked_tokens (
            jti VARCHAR(64) PRIMARY KEY,
            revoked_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
            reason TEXT
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS shares (
            id UUID PRIMARY KEY,
            file_id TEXT NOT NULL,
            created_by_user_id UUID,
            token VARCHAR(128) NOT NULL UNIQUE,
            permission VARCHAR(16) NOT NULL DEFAULT 'view',
            expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
            revoked_at TIMESTAMP WITHOUT TIME ZONE,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_shares_file_id ON shares (file_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_shares_token ON shares (token)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS job_failures (
            id UUID PRIMARY KEY,
            job_id TEXT,
            file_id TEXT,
            stage VARCHAR(32) NOT NULL,
            error_class VARCHAR(128) NOT NULL,
            message TEXT NOT NULL,
            traceback TEXT,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_events (
            id UUID PRIMARY KEY,
            event_type VARCHAR(64) NOT NULL,
            actor_user_id UUID,
            actor_anon_sub TEXT,
            file_id TEXT,
            data JSON,
            created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
        )
        """
    )

    op.execute("ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS owner_user_id UUID")
    op.execute("ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS owner_anon_sub TEXT")
    op.execute("ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS is_anonymous BOOLEAN DEFAULT true")
    op.execute("ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS privacy VARCHAR(16) DEFAULT 'private'")
    op.execute("ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS archived_at TIMESTAMP WITHOUT TIME ZONE")

    op.execute("UPDATE uploaded_files SET owner_anon_sub = owner_sub WHERE owner_anon_sub IS NULL")
    op.execute("UPDATE uploaded_files SET is_anonymous = true WHERE is_anonymous IS NULL")
    op.execute("UPDATE uploaded_files SET privacy = 'private' WHERE privacy IS NULL")


def downgrade() -> None:
    op.execute("ALTER TABLE uploaded_files DROP COLUMN IF EXISTS archived_at")
    op.execute("ALTER TABLE uploaded_files DROP COLUMN IF EXISTS privacy")
    op.execute("ALTER TABLE uploaded_files DROP COLUMN IF EXISTS is_anonymous")
    op.execute("ALTER TABLE uploaded_files DROP COLUMN IF EXISTS owner_anon_sub")
    op.execute("ALTER TABLE uploaded_files DROP COLUMN IF EXISTS owner_user_id")

    op.execute("DROP TABLE IF EXISTS audit_events")
    op.execute("DROP TABLE IF EXISTS job_failures")
    op.execute("DROP TABLE IF EXISTS shares")
    op.execute("DROP TABLE IF EXISTS revoked_tokens")
    op.execute("DROP TABLE IF EXISTS users")
