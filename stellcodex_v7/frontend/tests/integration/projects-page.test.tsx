import test from "node:test";
import { expectIncludes } from "../helpers/sourceTestUtils";

test("projects page composes typed filters and table surfaces", () => {
  expectIncludes("app/projects/page.tsx", ["useProjects", "ProjectsFilters", "ProjectsTable", 'title="Projects"']);
});
