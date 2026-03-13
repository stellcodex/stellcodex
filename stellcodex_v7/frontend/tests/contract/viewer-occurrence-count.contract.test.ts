import test from "node:test";
import { expectExcludes, expectIncludes } from "../helpers/sourceTestUtils";

test("viewer occurrence count derives from assembly hierarchy", () => {
  expectIncludes("lib/mappers/viewerMappers.ts", ["countOccurrences(nodes: ViewerOccurrenceNode[])", "totalOccurrences: countOccurrences(tree)"]);
  expectExcludes("lib/mappers/viewerMappers.ts", [/totalOccurrences:\s*.*renderBindings/i, /totalOccurrences:\s*.*gltf_nodes/i]);
});
