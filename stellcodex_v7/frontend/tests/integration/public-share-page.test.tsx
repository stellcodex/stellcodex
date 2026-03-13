import test from "node:test";
import { expectIncludes } from "../helpers/sourceTestUtils";

test("public share page differentiates valid, expired, revoked, and forbidden states", () => {
  expectIncludes("components/share/ShareViewerClient.tsx", ["PublicShareLayout", "PublicShareExpiredState", "PublicShareRevokedState", "PublicShareForbiddenState"]);
  expectIncludes("app/s/[token]/page.tsx", ["ShareViewerClient"]);
});
