import test from "node:test";
import { expectExcludes, expectIncludes } from "../helpers/sourceTestUtils";

test("file detail and viewer routes stay on fileId identity only", () => {
  expectIncludes("app/files/[fileId]/page.tsx", ["useParams<{ fileId: string }>()", "fileId"]);
  expectIncludes("app/files/[fileId]/viewer/page.tsx", ["useParams<{ fileId: string }>()", "fileId"]);
  expectExcludes("app/files/[fileId]/page.tsx", [/revision_id/i, /revisionId/]);
  expectExcludes("app/files/[fileId]/viewer/page.tsx", [/revision_id/i, /revisionId/]);
});

test("public share surface exposes safe file identity only", () => {
  expectIncludes("components/share/ShareViewerClient.tsx", ["Public file identity:"]);
  expectExcludes("components/share/ShareViewerClient.tsx", [/revision_id/i, /storage_key/i, /object_key/i]);
});
