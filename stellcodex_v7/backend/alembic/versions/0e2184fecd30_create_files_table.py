from alembic import op
import sqlalchemy as sa

revision = "0e2184fecd30"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Idempotent DDL: this repo may pre-create tables during startup.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS files (
            file_id VARCHAR(36) PRIMARY KEY,
            owner_sub TEXT NOT NULL,
            bucket TEXT NOT NULL,
            object_key TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            content_type VARCHAR(128) NOT NULL,
            size_bytes BIGINT NOT NULL,
            sha256 VARCHAR(64),
            gltf_key TEXT,
            thumbnail_key TEXT,
            metadata JSON NOT NULL DEFAULT '{}'::json,
            status VARCHAR(16) NOT NULL DEFAULT 'pending',
            visibility VARCHAR(16) NOT NULL DEFAULT 'private',
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now(),
            CONSTRAINT uq_files_object_key UNIQUE (object_key)
        )
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'files'
                  AND column_name = 'owner_sub'
            ) THEN
                EXECUTE 'CREATE INDEX IF NOT EXISTS ix_files_owner_sub ON files (owner_sub)';
            END IF;
        END
        $$;
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_files_owner_sub")
    op.execute("DROP TABLE IF EXISTS files")
