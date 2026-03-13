import test from "node:test";
import { expectIncludes } from "../helpers/sourceTestUtils";

test("file actions keep viewer and share routes on fileId", () => {
  expectIncludes("components/files/FileActions.tsx", ["href={`/files/${file.fileId}/viewer`}", 'href="/shares"']);
});
