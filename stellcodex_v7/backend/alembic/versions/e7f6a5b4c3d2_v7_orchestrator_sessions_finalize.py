"""finalize v7 orchestrator sessions contract + backfill

Revision ID: e7f6a5b4c3d2
Revises: c9a5f0f3e1b2
Create Date: 2026-03-07 05:40:00.000000
"""

from __future__ import annotations

from alembic import op


revision = "e7f6a5b4c3d2"
down_revision = "c9a5f0f3e1b2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE orchestrator_sessions
          ADD COLUMN IF NOT EXISTS state VARCHAR(8),
          ADD COLUMN IF NOT EXISTS rule_version VARCHAR(32),
          ADD COLUMN IF NOT EXISTS mode VARCHAR(32),
          ADD COLUMN IF NOT EXISTS confidence DOUBLE PRECISION
        """
    )

    op.execute(
        """
        ALTER TABLE orchestrator_sessions
        ALTER COLUMN risk_flags TYPE JSONB USING COALESCE(risk_flags::jsonb, '[]'::jsonb)
        """
    )
    op.execute(
        """
        ALTER TABLE orchestrator_sessions
        ALTER COLUMN decision_json TYPE JSONB USING COALESCE(decision_json::jsonb, '{}'::jsonb)
        """
    )
    op.execute(
        """
        ALTER TABLE rule_configs
        ALTER COLUMN value_json TYPE JSONB USING COALESCE(value_json::jsonb, '{}'::jsonb)
        """
    )
    op.execute(
        """
        ALTER TABLE uploaded_files
        ALTER COLUMN decision_json TYPE JSONB USING COALESCE(decision_json::jsonb, '{}'::jsonb)
        """
    )

    op.execute("ALTER TABLE orchestrator_sessions ALTER COLUMN decision_json SET DEFAULT '{}'::jsonb")
    op.execute("UPDATE orchestrator_sessions SET decision_json = '{}'::jsonb WHERE decision_json IS NULL")
    op.execute("ALTER TABLE orchestrator_sessions ALTER COLUMN decision_json SET NOT NULL")

    op.execute(
        """
        UPDATE orchestrator_sessions
        SET
          state = COALESCE(
            NULLIF(state, ''),
            NULLIF(state_code, ''),
            CASE
              WHEN COALESCE(NULLIF(status_gate, ''), 'PENDING') = 'REJECTED' THEN 'S4'
              WHEN COALESCE(NULLIF(status_gate, ''), 'PENDING') = 'NEEDS_APPROVAL' THEN 'S5'
              WHEN COALESCE(NULLIF(status_gate, ''), 'PENDING') = 'PASS' THEN 'S6'
              ELSE 'S0'
            END
          ),
          rule_version = COALESCE(
            NULLIF(rule_version, ''),
            NULLIF(decision_json->>'rule_version', ''),
            'v7.0.0'
          ),
          mode = COALESCE(
            NULLIF(mode, ''),
            NULLIF(decision_json->>'mode', ''),
            'visual_only'
          ),
          confidence = COALESCE(
            confidence,
            CASE
              WHEN (decision_json->>'confidence') ~ '^[0-9]+(\\.[0-9]+)?$'
                THEN (decision_json->>'confidence')::double precision
              ELSE NULL
            END,
            0.05
          )
        """
    )

    op.execute(
        """
        UPDATE orchestrator_sessions
        SET
          state = CASE
            WHEN state IN ('S0','S1','S2','S3','S4','S5','S6','S7') THEN state
            ELSE 'S0'
          END,
          state_code = CASE
            WHEN COALESCE(NULLIF(state,''), 'S0') IN ('S0','S1','S2','S3','S4','S5','S6','S7')
              THEN COALESCE(NULLIF(state,''), 'S0')
            ELSE 'S0'
          END,
          state_label = CASE COALESCE(NULLIF(state,''), 'S0')
            WHEN 'S0' THEN 'uploaded'
            WHEN 'S1' THEN 'converted'
            WHEN 'S2' THEN 'assembly_ready'
            WHEN 'S3' THEN 'analyzing'
            WHEN 'S4' THEN 'dfm_ready'
            WHEN 'S5' THEN 'awaiting_approval'
            WHEN 'S6' THEN 'approved'
            WHEN 'S7' THEN 'share_ready'
            ELSE 'uploaded'
          END,
          status_gate = CASE
            WHEN COALESCE(NULLIF(status_gate, ''), 'PENDING') IN ('PENDING','PASS','NEEDS_APPROVAL','REJECTED')
              THEN COALESCE(NULLIF(status_gate, ''), 'PENDING')
            WHEN COALESCE(NULLIF(state,''), 'S0') = 'S5' THEN 'NEEDS_APPROVAL'
            WHEN COALESCE(NULLIF(state,''), 'S0') IN ('S6','S7') THEN 'PASS'
            ELSE 'PENDING'
          END,
          confidence = LEAST(1.0, GREATEST(0.0, COALESCE(confidence, 0.05))),
          mode = CASE
            WHEN LOWER(COALESCE(mode, '')) IN ('brep','mesh_approx','visual_only') THEN LOWER(mode)
            ELSE 'visual_only'
          END,
          rule_version = COALESCE(NULLIF(rule_version, ''), 'v7.0.0')
        """
    )

    op.execute(
        """
        UPDATE orchestrator_sessions
        SET decision_json = (
          COALESCE(decision_json, '{}'::jsonb)
          || jsonb_build_object(
            'schema', COALESCE(NULLIF(decision_json->>'schema', ''), 'stellcodex.v7.decision_json'),
            'version', COALESCE(NULLIF(decision_json->>'version', ''), '1.1'),
            'state', state,
            'state_code', state,
            'state_label', state_label,
            'status_gate', status_gate,
            'approval_required', COALESCE(approval_required, false),
            'rule_version', rule_version,
            'mode', mode,
            'confidence', confidence,
            'manufacturing_method', COALESCE(NULLIF(decision_json->>'manufacturing_method', ''), 'manual_review'),
            'conflict_flags',
              CASE
                WHEN jsonb_typeof(decision_json->'conflict_flags') = 'array'
                  THEN decision_json->'conflict_flags'
                ELSE '[]'::jsonb
              END
          )
        )
        """
    )

    op.execute(
        """
        UPDATE orchestrator_sessions
        SET decision_json = jsonb_set(
          decision_json,
          '{rule_explanations}',
          '["legacy_backfill: session normalized to V7 canonical contract."]'::jsonb,
          true
        )
        WHERE
          COALESCE(jsonb_typeof(decision_json->'rule_explanations'), 'null') <> 'array'
          OR jsonb_array_length(
            CASE
              WHEN jsonb_typeof(decision_json->'rule_explanations') = 'array'
                THEN decision_json->'rule_explanations'
              ELSE '[]'::jsonb
            END
          ) = 0
        """
    )

    op.execute("ALTER TABLE orchestrator_sessions ALTER COLUMN state SET DEFAULT 'S0'")
    op.execute("ALTER TABLE orchestrator_sessions ALTER COLUMN state SET NOT NULL")
    op.execute("ALTER TABLE orchestrator_sessions ALTER COLUMN rule_version SET DEFAULT 'v7.0.0'")
    op.execute("ALTER TABLE orchestrator_sessions ALTER COLUMN rule_version SET NOT NULL")
    op.execute("ALTER TABLE orchestrator_sessions ALTER COLUMN mode SET DEFAULT 'visual_only'")
    op.execute("ALTER TABLE orchestrator_sessions ALTER COLUMN mode SET NOT NULL")
    op.execute("ALTER TABLE orchestrator_sessions ALTER COLUMN confidence SET DEFAULT 0.05")
    op.execute("ALTER TABLE orchestrator_sessions ALTER COLUMN confidence SET NOT NULL")

    op.execute(
        """
        INSERT INTO rule_configs (id, key, value_json, enabled, description)
        VALUES
          ('5e6b7c20-1324-4a12-9e45-a9ccda100007'::uuid, 'rule_version', jsonb_build_object('value', 'v7.0.0', 'version', 'v7.0.0', 'scope', 'global'), true, 'Canonical rule config version for deterministic decisions'),
          ('5e6b7c20-1324-4a12-9e45-a9ccda100008'::uuid, 'legacy_backfill_confidence', jsonb_build_object('value', 0.05, 'version', 'v7.0.0', 'scope', 'global'), true, 'Fallback confidence for legacy/backfilled sessions'),
          ('5e6b7c20-1324-4a12-9e45-a9ccda100009'::uuid, 'manufacturing_unknown_confidence_floor', jsonb_build_object('value', 0.1, 'version', 'v7.0.0', 'scope', 'global'), true, 'Minimum confidence floor when manufacturing method is unknown'),
          ('5e6b7c20-1324-4a12-9e45-a9ccda10000a'::uuid, 'manufacturing_fallback_method', jsonb_build_object('value', 'manual_review', 'version', 'v7.0.0', 'scope', 'global'), true, 'Fallback manufacturing method when geometry is insufficient')
        ON CONFLICT (key) DO NOTHING
        """
    )

    op.execute(
        """
        UPDATE rule_configs
        SET value_json = jsonb_build_object(
          'value', CASE
            WHEN jsonb_typeof(value_json) = 'object' AND value_json ? 'value' THEN value_json->'value'
            WHEN jsonb_typeof(value_json) = 'object' THEN to_jsonb(value_json)
            ELSE to_jsonb(value_json)
          END,
          'version', COALESCE(
            CASE WHEN jsonb_typeof(value_json) = 'object' THEN NULLIF(value_json->>'version', '') ELSE NULL END,
            'v7.0.0'
          ),
          'scope', COALESCE(
            CASE WHEN jsonb_typeof(value_json) = 'object' THEN NULLIF(value_json->>'scope', '') ELSE NULL END,
            'global'
          )
        )
        WHERE value_json IS NOT NULL
        """
    )

    op.execute("ALTER TABLE uploaded_files ALTER COLUMN decision_json SET DEFAULT '{}'::jsonb")
    op.execute("UPDATE uploaded_files SET decision_json = '{}'::jsonb WHERE decision_json IS NULL")
    op.execute("ALTER TABLE uploaded_files ALTER COLUMN decision_json SET NOT NULL")


def downgrade() -> None:
    op.execute("ALTER TABLE orchestrator_sessions DROP COLUMN IF EXISTS confidence")
    op.execute("ALTER TABLE orchestrator_sessions DROP COLUMN IF EXISTS mode")
    op.execute("ALTER TABLE orchestrator_sessions DROP COLUMN IF EXISTS rule_version")
    op.execute("ALTER TABLE orchestrator_sessions DROP COLUMN IF EXISTS state")
