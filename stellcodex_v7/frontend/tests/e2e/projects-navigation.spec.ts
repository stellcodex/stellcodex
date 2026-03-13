import test from "node:test";
import { expectIncludes } from "../helpers/sourceTestUtils";

test("project navigation opens project and file routes by projectId/fileId", () => {
  expectIncludes("components/projects/ProjectsTable.tsx", ["href={`/projects/${row.projectId}`}", "Open"]);
  expectIncludes("components/projects/ProjectFilesTable.tsx", ["href={`/files/${file.fileId}`}", "href={`/files/${file.fileId}/viewer`}"]);
});
