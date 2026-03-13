import type {
  DecisionSummary,
  OrchestratorStateSummary,
  RequiredInputField,
} from "@/lib/contracts/orchestrator";

type RawRecord = Record<string, unknown>;

export function mapOrchestratorState(input: unknown): OrchestratorStateSummary {
  const row = (input && typeof input === "object" ? input : {}) as RawRecord;
  const statusGate = typeof row.status_gate === "string" ? row.status_gate : null;
  const approvalRequired = Boolean(row.approval_required);
  return {
    sessionId: typeof row.session_id === "string" ? row.session_id : null,
    stateCode: typeof row.state_code === "string" ? row.state_code : typeof row.state === "string" ? row.state : "S0",
    stateLabel: typeof row.state_label === "string" ? row.state_label : null,
    blocked: statusGate === "REJECTED",
    blockedReason:
      statusGate === "REJECTED"
        ? "Decision rejected by deterministic policy"
        : approvalRequired
        ? "Approval required before release"
        : null,
    approvalRequired,
    startedAt: typeof row.created_at === "string" ? row.created_at : null,
    updatedAt: typeof row.updated_at === "string" ? row.updated_at : null,
    progressLabel: statusGate || null,
    statusGate,
  };
}

export function mapDecisionSummary(input: unknown): DecisionSummary {
  const row = (input && typeof input === "object" ? input : {}) as RawRecord;
  return {
    manufacturingMethod:
      typeof row.manufacturing_method === "string"
        ? row.manufacturing_method
        : typeof (row.decision_json as RawRecord | undefined)?.manufacturing_method === "string"
        ? ((row.decision_json as RawRecord).manufacturing_method as string)
        : null,
    mode:
      typeof row.mode === "string"
        ? row.mode
        : typeof (row.decision_json as RawRecord | undefined)?.mode === "string"
        ? ((row.decision_json as RawRecord).mode as string)
        : null,
    confidence:
      typeof row.confidence === "number"
        ? row.confidence
        : typeof (row.decision_json as RawRecord | undefined)?.confidence === "number"
        ? ((row.decision_json as RawRecord).confidence as number)
        : null,
    ruleVersion:
      typeof row.rule_version === "string"
        ? row.rule_version
        : typeof (row.decision_json as RawRecord | undefined)?.rule_version === "string"
        ? ((row.decision_json as RawRecord).rule_version as string)
        : null,
    explanations: Array.isArray(row.rule_explanations)
      ? row.rule_explanations.filter((item): item is string => typeof item === "string")
      : [],
    warnings: Array.isArray(row.conflict_flags)
      ? row.conflict_flags.filter((item): item is string => typeof item === "string")
      : [],
    updatedAt: typeof row.updated_at === "string" ? row.updated_at : null,
  };
}

export function mapRequiredInputs(): RequiredInputField[] {
  return [];
}
