import test from "node:test";
import { expectIncludes, expectExcludes } from "../helpers/sourceTestUtils";

test("assembly tree reflects occurrence hierarchy instead of mesh counts", () => {
  expectIncludes("lib/mappers/viewerMappers.ts", ["occurrencePath", "childCount", "children,"]);
  expectExcludes("lib/mappers/viewerMappers.ts", [/part count/i, /mesh count/i]);
});
