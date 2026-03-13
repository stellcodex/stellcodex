import test from "node:test";
import { expectIncludes } from "../helpers/sourceTestUtils";

test("expired shares map HTTP 410 to a terminal expired state", () => {
  expectIncludes("lib/hooks/useShares.ts", ["nextError.status === 410", 'mapPublicShareStatus(token, "expired")']);
  expectIncludes("components/share/ShareViewerClient.tsx", ["PublicShareExpiredState"]);
});
