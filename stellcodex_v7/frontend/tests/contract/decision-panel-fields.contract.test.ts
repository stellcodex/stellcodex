import test from "node:test";
import { expectIncludes } from "../helpers/sourceTestUtils";

test("decision panel shows mode, confidence, and rule version", () => {
  expectIncludes("components/intelligence/DecisionPanel.tsx", ["Mode", "Confidence", "Rule version"]);
});
