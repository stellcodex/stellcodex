import test from "node:test";
import { expectIncludes } from "../helpers/sourceTestUtils";

test("share create and open flow stays wired to public URLs", () => {
  expectIncludes("components/shares/ShareCreateForm.tsx", ["Create share", "expiresInSeconds"]);
  expectIncludes("components/shares/ShareTable.tsx", ["share.publicUrl", "target=\"_blank\"", "ShareRevokeDialog"]);
});
