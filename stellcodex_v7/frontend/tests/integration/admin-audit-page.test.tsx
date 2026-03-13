import test from "node:test";
import { expectIncludes } from "../helpers/sourceTestUtils";

test("admin audit page renders the audit table only", () => {
  expectIncludes("app/(app)/admin/audit/page.tsx", ["useAdminQueues", "AuditTable"]);
});
