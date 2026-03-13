import test from "node:test";
import { expectIncludes } from "../helpers/sourceTestUtils";

test("shares page renders create and revoke flow surfaces", () => {
  expectIncludes("app/(app)/shares/page.tsx", ["ShareDialog", "ShareTable", "useShares", "Create share"]);
});
