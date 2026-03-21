from __future__ import annotations

import sys
import unittest
import uuid
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR_STR = str(BACKEND_DIR)
if BACKEND_DIR_STR not in sys.path:
    sys.path.insert(0, BACKEND_DIR_STR)

from app.models.rule_config import RuleConfig  # noqa: E402
from app.services.orchestrator_sessions import build_decision_json, normalize_decision_mode  # noqa: E402
from app.services.rule_configs import HYBRID_V1_RULE_CONFIG_KEY, load_hybrid_v1_config  # noqa: E402


class _FakeQuery:
    def __init__(self, rows):
        self._rows = rows

    def filter(self, *_args, **_kwargs):
        return self

    def all(self):
        return list(self._rows)


class _FakeSession:
    def __init__(self, rows):
        self._rows = rows

    def query(self, _model):
        return _FakeQuery(self._rows)


class V7RuleConfigRuntimeTests(unittest.TestCase):
    def test_global_and_project_rule_configs_override_defaults(self) -> None:
        project_id = uuid.uuid4()
        rows = [
            RuleConfig(
                scope="global",
                scope_id=None,
                key=HYBRID_V1_RULE_CONFIG_KEY,
                value_json={"wall_mm_min": 1.4, "runner_mode_default": "cold"},
                version="v1.1",
            ),
            RuleConfig(
                scope="project",
                scope_id=project_id,
                key=HYBRID_V1_RULE_CONFIG_KEY,
                value_json={"draft_min_deg": 2.5},
                version="v1.2-project",
            ),
        ]
        session = _FakeSession(rows)

        config, version = load_hybrid_v1_config(session, project_id=project_id)

        self.assertEqual(config["wall_mm_min"], 1.4)
        self.assertEqual(config["draft_min_deg"], 2.5)
        self.assertEqual(version, "v1.2-project")

    def test_decision_json_fallback_is_schema_shaped(self) -> None:
        decision_json = build_decision_json(mode="doc", rule_version="v2.0")

        self.assertEqual(normalize_decision_mode("doc"), "visual_only")
        self.assertEqual(decision_json["rule_version"], "v2.0")
        self.assertEqual(decision_json["mode"], "visual_only")
        self.assertIn("confidence", decision_json)
        self.assertIn("manufacturing_method", decision_json)
        self.assertIsInstance(decision_json["rule_explanations"], list)
        self.assertGreaterEqual(len(decision_json["rule_explanations"]), 1)
        self.assertIsInstance(decision_json["conflict_flags"], list)

    def test_live_rule_config_key_value_rows_override_defaults(self) -> None:
        rows = [
            RuleConfig(key="rule_version", value_json={"scope": "global", "value": "v7.0.0", "version": "v7.0.0"}),
            RuleConfig(key="draft_min_deg", value_json={"scope": "global", "value": 1.8, "version": "v7.0.0"}),
            RuleConfig(key="wall_mm_min", value_json={"scope": "global", "value": 1.2, "version": "v7.0.0"}),
            RuleConfig(key="allow_hot_runner", value_json={"scope": "global", "value": False, "version": "v7.0.0"}),
        ]
        session = _FakeSession(rows)

        config, version = load_hybrid_v1_config(session, project_id="default")

        self.assertEqual(config["draft_min_deg"], 1.8)
        self.assertEqual(config["wall_mm_min"], 1.2)
        self.assertEqual(config["hot_runner"], "needs_approval")
        self.assertEqual(version, "v7.0.0")


if __name__ == "__main__":
    unittest.main()
