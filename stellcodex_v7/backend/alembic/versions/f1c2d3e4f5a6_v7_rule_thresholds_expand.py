"""expand v7 deterministic rule threshold configs

Revision ID: f1c2d3e4f5a6
Revises: e7f6a5b4c3d2
Create Date: 2026-03-07 21:10:00.000000
"""

from __future__ import annotations

from alembic import op


revision = "f1c2d3e4f5a6"
down_revision = "e7f6a5b4c3d2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO rule_configs (id, key, value_json, enabled, description)
        VALUES
          ('5e6b7c20-1324-4a12-9e45-a9ccda100101'::uuid, 'quantity_threshold_high', jsonb_build_object('value', 500, 'version', 'v7.0.0', 'scope', 'global'), true, 'Quantity threshold triggering high-volume deterministic review'),
          ('5e6b7c20-1324-4a12-9e45-a9ccda100102'::uuid, 'tolerance_mm_tight', jsonb_build_object('value', 0.05, 'version', 'v7.0.0', 'scope', 'global'), true, 'Tolerance threshold requiring precision process review'),
          ('5e6b7c20-1324-4a12-9e45-a9ccda100103'::uuid, 'undercut_count_warn', jsonb_build_object('value', 1, 'version', 'v7.0.0', 'scope', 'global'), true, 'Undercut count threshold requiring tooling review'),
          ('5e6b7c20-1324-4a12-9e45-a9ccda100104'::uuid, 'shrinkage_warn_pct', jsonb_build_object('value', 2.0, 'version', 'v7.0.0', 'scope', 'global'), true, 'Shrinkage percentage warning threshold'),
          ('5e6b7c20-1324-4a12-9e45-a9ccda100105'::uuid, 'shrinkage_block_pct', jsonb_build_object('value', 4.0, 'version', 'v7.0.0', 'scope', 'global'), true, 'Shrinkage percentage hard-block threshold'),
          ('5e6b7c20-1324-4a12-9e45-a9ccda100106'::uuid, 'volume_mm3_high', jsonb_build_object('value', 1000000, 'version', 'v7.0.0', 'scope', 'global'), true, 'High volume threshold for process conflict checks'),
          ('5e6b7c20-1324-4a12-9e45-a9ccda100107'::uuid, 'volume_quantity_conflict_limit', jsonb_build_object('value', 50000000, 'version', 'v7.0.0', 'scope', 'global'), true, 'Volume*quantity conflict limit')
        ON CONFLICT (key) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM rule_configs
        WHERE key IN (
          'quantity_threshold_high',
          'tolerance_mm_tight',
          'undercut_count_warn',
          'shrinkage_warn_pct',
          'shrinkage_block_pct',
          'volume_mm3_high',
          'volume_quantity_conflict_limit'
        )
        """
    )
