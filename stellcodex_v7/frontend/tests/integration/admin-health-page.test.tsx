import test from "node:test";
import { expectIncludes } from "../helpers/sourceTestUtils";

test("admin health page renders safe summary data", () => {
  expectIncludes("app/(app)/admin/health/page.tsx", ["useAdminHealth", "HealthSummary"]);
});
