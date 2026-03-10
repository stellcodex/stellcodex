from __future__ import annotations

import unittest

from app.stell_ai.planner import build_plan


class StellAIPlannerTests(unittest.TestCase):
    def test_build_plan_includes_file_id_for_file_scoped_tools(self) -> None:
        plan = build_plan(
            goal="file dfm status",
            file_ids=["scx_123"],
            allowed_tools=frozenset({"files.status", "dfm.report", "knowledge.search"}),
        )

        steps = {step.tool: step for step in plan.steps}
        self.assertEqual(steps["files.status"].arguments["file_id"], "scx_123")
        self.assertEqual(steps["dfm.report"].arguments["file_id"], "scx_123")

    def test_build_plan_skips_report_tool_and_file_scoped_tools_without_file_ids(self) -> None:
        plan = build_plan(
            goal="generate report for uploaded files",
            file_ids=[],
            allowed_tools=frozenset({"files.status", "report.generate", "knowledge.search"}),
        )

        tools = [step.tool for step in plan.steps]
        self.assertNotIn("report.generate", tools)
        self.assertNotIn("files.status", tools)
        self.assertIn("knowledge.search", tools)


if __name__ == "__main__":
    unittest.main()
