import test from "node:test";
import { expectIncludes } from "../helpers/sourceTestUtils";

test("file detail page renders versions, workflow, status, and shares", () => {
  expectIncludes("app/files/[fileId]/page.tsx", ["FileHeader", "FileSummaryCard", "FileWorkflowPanel", "FileSharesPanel", "FileStatusTimeline", "FileVersionsTable"]);
});
