-- V7 Migration 0002: rule_configs (threshold/config store)

CREATE TABLE IF NOT EXISTS rule_configs (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scope       TEXT NOT NULL DEFAULT 'global',   -- global|tenant|project
  scope_id    UUID NULL,
  key         TEXT NOT NULL,
  value_json  JSONB NOT NULL,
  version     TEXT NOT NULL DEFAULT 'v0.0',
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_rule_config_scope_key
  ON rule_configs(scope, scope_id, key);
