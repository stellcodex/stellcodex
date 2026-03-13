import test from "node:test";
import { expectIncludes } from "../helpers/sourceTestUtils";

test("revoked shares map to a terminal revoked state", () => {
  expectIncludes("lib/hooks/useShares.ts", ["nextError.status === 403", 'mapPublicShareStatus(token, "revoked")']);
  expectIncludes("components/share/ShareViewerClient.tsx", ["PublicShareRevokedState"]);
});
