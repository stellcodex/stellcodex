import test from "node:test";
import { expectIncludes } from "../helpers/sourceTestUtils";

test("approval state remains visible and actionable when required", () => {
  expectIncludes("components/intelligence/ApprovalPanel.tsx", ["ApprovalStatusBadge", "approvalRequired ? (", "Approve", "Reject"]);
});
