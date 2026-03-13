export type OrchestratorStateSummary = {
  sessionId?: string | null;
  stateCode: string;
  stateLabel?: string | null;
  blocked?: boolean;
  blockedReason?: string | null;
  approvalRequired?: boolean;
  startedAt?: string | null;
  updatedAt?: string | null;
  progressLabel?: string | null;
  statusGate?: string | null;
};

export type RequiredInputField = {
  key: string;
  label: string;
  type: "text" | "number" | "select" | "boolean" | "multiselect" | "textarea";
  required: boolean;
  helpText?: string;
  options?: Array<{ label: string; value: string }>;
  value?: string | number | boolean | string[] | null;
  error?: string | null;
};

export type DecisionSummary = {
  manufacturingMethod?: string | null;
  mode?: "brep" | "mesh_approx" | "visual_only" | string | null;
  confidence?: number | null;
  ruleVersion?: string | null;
  explanations: string[];
  warnings: string[];
  updatedAt?: string | null;
};
