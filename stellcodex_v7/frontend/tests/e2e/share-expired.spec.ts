import test from "node:test";
import { expectIncludes } from "../helpers/sourceTestUtils";

test("expired shares stay terminal and do not render the valid viewer", () => {
  expectIncludes("components/share/ShareViewerClient.tsx", ['if (!data || data.status === "expired") return <PublicShareExpiredState />']);
});
