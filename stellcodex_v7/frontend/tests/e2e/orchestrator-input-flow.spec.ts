import test from "node:test";
import { expectIncludes } from "../helpers/sourceTestUtils";

test("viewer intelligence panel keeps required inputs and approval flow wired", () => {
  expectIncludes("components/intelligence/IntelligencePanel.tsx", ["StatePanel", "RequiredInputsPanel", "DecisionPanel", "RisksPanel", "DfmReportPanel", "ActivityEvidencePanel", "ApprovalPanel"]);
  expectIncludes("components/intelligence/RequiredInputsForm.tsx", ["Checkbox", "Input", "Select", "Textarea", "Submit inputs"]);
});
