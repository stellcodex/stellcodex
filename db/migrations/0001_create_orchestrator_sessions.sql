-- V7 Migration 0001: orchestrator_sessions
-- Note: adjust FK types/names to your existing schema conventions.

CREATE TABLE IF NOT EXISTS orchestrator_sessions (
  id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  file_id           UUID NOT NULL,
  state             TEXT NOT NULL,
  decision_json     JSONB NOT NULL DEFAULT '{}'::jsonb,
  rule_version      TEXT NOT NULL DEFAULT 'v0.0',
  mode              TEXT NOT NULL DEFAULT 'visual_only',
  confidence        DOUBLE PRECISION NOT NULL DEFAULT 0.0,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_orch_file_id ON orchestrator_sessions(file_id);
CREATE INDEX IF NOT EXISTS idx_orch_state ON orchestrator_sessions(state);
