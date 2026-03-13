import test from "node:test";
import { expectIncludes } from "../helpers/sourceTestUtils";

test("viewer fails closed without assembly metadata", () => {
  expectIncludes("lib/mappers/viewerMappers.ts", ['if (viewerKind === "3d" && !hasAssemblyMeta)', 'status: "unavailable"', "Viewer unavailable: assembly metadata missing"]);
  expectIncludes("components/viewer/AssemblyTree.tsx", ["Viewer unavailable: assembly metadata missing"]);
});
