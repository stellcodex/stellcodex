"""add tenant ownership to uploaded_files and backfill

Revision ID: h4d5e6f7a8b9
Revises: g2a3b4c5d6e7
Create Date: 2026-03-08 06:05:00.000000
"""

from __future__ import annotations

from alembic import op


revision = "h4d5e6f7a8b9"
down_revision = "g2a3b4c5d6e7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE uploaded_files ADD COLUMN IF NOT EXISTS tenant_id BIGINT")
    op.execute("CREATE INDEX IF NOT EXISTS ix_uploaded_files_tenant_id ON uploaded_files (tenant_id)")

    op.execute(
        """
        INSERT INTO tenants (code, name)
        SELECT DISTINCT
            'owner-' || substr(md5(coalesce(owner_sub, 'anonymous')), 1, 24) AS code,
            'Owner ' || substr(md5(coalesce(owner_sub, 'anonymous')), 1, 12) AS name
        FROM uploaded_files
        ON CONFLICT (code) DO NOTHING
        """
    )

    op.execute(
        """
        UPDATE uploaded_files uf
        SET tenant_id = t.id
        FROM tenants t
        WHERE uf.tenant_id IS NULL
          AND t.code = 'owner-' || substr(md5(coalesce(uf.owner_sub, 'anonymous')), 1, 24)
        """
    )

    op.execute("ALTER TABLE uploaded_files ALTER COLUMN tenant_id SET NOT NULL")
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_uploaded_files_tenant'
            ) THEN
                ALTER TABLE uploaded_files
                ADD CONSTRAINT fk_uploaded_files_tenant
                FOREIGN KEY (tenant_id) REFERENCES tenants(id);
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute("ALTER TABLE uploaded_files DROP CONSTRAINT IF EXISTS fk_uploaded_files_tenant")
    op.execute("DROP INDEX IF EXISTS ix_uploaded_files_tenant_id")
    op.execute("ALTER TABLE uploaded_files DROP COLUMN IF EXISTS tenant_id")
