import test from "node:test";
import { expectIncludes } from "../helpers/sourceTestUtils";

test("disabled buttons guard important actions", () => {
  expectIncludes("components/primitives/Button.tsx", ["disabled={disabled || loading}"]);
  expectIncludes("components/intelligence/ApprovalPanel.tsx", ["disabled={!onReject || busy}", "disabled={!onApprove}"]);
  expectIncludes("components/shares/ShareCreateForm.tsx", ["const invalid =", '<Button variant="primary" disabled={invalid}']);
});
