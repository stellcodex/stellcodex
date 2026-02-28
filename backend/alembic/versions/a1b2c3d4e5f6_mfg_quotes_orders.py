"""mfg quotes + production orders tables

Revision ID: a1b2c3d4e5f6
Revises: f4b1a2c3d4e5
Create Date: 2026-02-27 21:00:00.000000
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "f4b1a2c3d4e5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Idempotent DDL so existing manually-created tables are preserved.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS quotes (
            quote_id VARCHAR(80) PRIMARY KEY,
            quote_number VARCHAR(30) NOT NULL,
            file_id VARCHAR(40) NOT NULL,
            owner_sub TEXT NOT NULL,
            filename TEXT NOT NULL,
            process VARCHAR(32) NOT NULL,
            process_label TEXT NOT NULL,
            material_id VARCHAR(32) NOT NULL,
            material_label TEXT NOT NULL,
            currency VARCHAR(8) DEFAULT 'EUR',
            payment_terms TEXT NOT NULL,
            issued_date VARCHAR(10) NOT NULL,
            valid_until VARCHAR(10) NOT NULL,
            status VARCHAR(16) DEFAULT 'pending',
            document_json JSONB NOT NULL,
            geometry_summary JSONB,
            breakdown_json JSONB,
            qty_breaks_json JSONB,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS production_orders (
            order_id VARCHAR(40) PRIMARY KEY,
            order_number VARCHAR(30) NOT NULL,
            quote_id VARCHAR(80) NOT NULL,
            file_id VARCHAR(40) NOT NULL,
            owner_sub TEXT NOT NULL,
            qty INTEGER NOT NULL,
            unit_price_eur DOUBLE PRECISION NOT NULL,
            total_eur DOUBLE PRECISION NOT NULL,
            lead_days INTEGER NOT NULL,
            currency VARCHAR(8) DEFAULT 'EUR',
            status VARCHAR(24) DEFAULT 'queued',
            notes TEXT,
            customer_po TEXT,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ DEFAULT now()
        )
        """
    )

    op.execute("CREATE INDEX IF NOT EXISTS ix_quotes_quote_number ON quotes (quote_number)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_quotes_file_id ON quotes (file_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_quotes_owner_sub ON quotes (owner_sub)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_quotes_status ON quotes (status)")

    op.execute("CREATE INDEX IF NOT EXISTS ix_po_quote_id ON production_orders (quote_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_po_file_id ON production_orders (file_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_po_owner_sub ON production_orders (owner_sub)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_po_status ON production_orders (status)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS production_orders")
    op.execute("DROP TABLE IF EXISTS quotes")
