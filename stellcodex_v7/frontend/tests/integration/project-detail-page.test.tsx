import test from "node:test";
import { expectIncludes } from "../helpers/sourceTestUtils";

test("project detail page renders summary, workflow, activity, and file list", () => {
  expectIncludes("app/projects/[projectId]/page.tsx", ["ProjectHeader", "ProjectSummaryPanel", "ProjectWorkflowSummaryPanel", "ProjectActivityPanel", "ProjectFilesTable"]);
});
