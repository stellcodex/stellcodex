import test from "node:test";
import { expectIncludes } from "../helpers/sourceTestUtils";

test("viewer page composes left tree, canvas, and intelligence panel", () => {
  expectIncludes("app/files/[fileId]/viewer/page.tsx", ["ViewerLayout", "AssemblyTree", "ViewerCanvas", "IntelligencePanel", "visibilityHint="]);
});
