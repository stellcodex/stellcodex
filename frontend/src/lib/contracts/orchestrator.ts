export interface RawDecisionExplanation {
  rule_id: string;
  triggered: boolean;
  severity: string;
  reference: string;
  reasoning: string;
}

export interface RawDecisionJson {
  rule_version: string;
  mode: string;
  confidence: number;
  manufacturing_method: string;
  rule_explanations: RawDecisionExplanation[];
  conflict_flags: string[];
}

export interface RawOrchestratorSession {
  session_id: string;
  file_id: string;
  state: string;
  state_label: string;
  approval_required: boolean;
  risk_flags: string[];
  decision_json: RawDecisionJson;
}

export interface RawRequiredInput {
  key: string;
  label: string;
  input_type: string;
  required: boolean;
}

export interface RawRequiredInputs {
  session_id: string;
  file_id: string;
  required_inputs: RawRequiredInput[];
}

export interface RawApprovalResponse {
  session_id: string;
  file_id: string;
  state: string;
  state_label: string;
  approval_required: boolean;
  decision_json: RawDecisionJson;
}
