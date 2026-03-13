import test from "node:test";
import { expectIncludes, expectExcludes } from "../helpers/sourceTestUtils";

test("viewer opens by fileId and not by revision identity", () => {
  expectIncludes("components/files/FileActions.tsx", ["href={`/files/${file.fileId}/viewer`}"]);
  expectExcludes("components/files/FileActions.tsx", [/revision_id/i, /revisionId/]);
});
