import test from "node:test";
import { expectIncludes } from "../helpers/sourceTestUtils";

test("admin pages stay dense and safe", () => {
  expectIncludes("app/(app)/admin/health/page.tsx", ["HealthSummary"]);
  expectIncludes("app/(app)/admin/audit/page.tsx", ["AuditTable"]);
});
