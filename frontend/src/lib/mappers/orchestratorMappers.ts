import type { RawDfmReport } from "@/lib/contracts/dfm";
import type {
  RawApprovalResponse,
  RawOrchestratorSession,
  RawRequiredInputs,
} from "@/lib/contracts/orchestrator";
import type { DecisionRecord, DfmRecord, RequiredInputRecord } from "@/lib/contracts/ui";

function mapDecisionBase(input: RawOrchestratorSession | RawApprovalResponse): DecisionRecord {
  return {
    sessionId: input.session_id,
    fileId: input.file_id,
    stateCode: input.state,
    stateLabel: input.state_label,
    approvalRequired: input.approval_required,
    riskFlags: "risk_flags" in input ? input.risk_flags : input.decision_json.conflict_flags,
    manufacturingMethod: input.decision_json.manufacturing_method,
    mode: input.decision_json.mode,
    confidence: input.decision_json.confidence,
    ruleVersion: input.decision_json.rule_version,
    explanations: (input.decision_json.rule_explanations ?? []).map((item) => ({
      ruleId: item.rule_id,
      triggered: item.triggered,
      severity: item.severity,
      reference: item.reference,
      reasoning: item.reasoning,
    })),
  };
}

export function mapDecisionRecord(input: RawOrchestratorSession | RawApprovalResponse) {
  return mapDecisionBase(input);
}

export function mapRequiredInputRecords(input: RawRequiredInputs): RequiredInputRecord[] {
  return input.required_inputs.map((item) => ({
    key: item.key,
    label: item.label,
    inputType: item.input_type,
    required: item.required,
  }));
}

export function mapDfmRecord(input: RawDfmReport): DfmRecord {
  return {
    fileId: input.file_id,
    statusGate: input.status_gate,
    riskFlags: input.risk_flags ?? [],
    findings: (input.findings ?? []).map((item) => ({
      code: item.code || "rule",
      severity: item.severity || "info",
      message: item.message || "No detail provided.",
      recommendation: item.recommendation ?? null,
      fields: item.fields ?? [],
    })),
    geometryReport: input.geometry_report ?? {},
  };
}
