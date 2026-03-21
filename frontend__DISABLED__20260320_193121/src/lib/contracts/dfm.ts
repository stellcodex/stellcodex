import type { RawDecisionJson } from "./orchestrator";

export interface RawDfmFinding {
  code?: string;
  severity?: string;
  message?: string;
  fields?: string[];
  recommendation?: string;
}

export interface RawDfmReport {
  file_id: string;
  status_gate: string;
  risk_flags: string[];
  findings: RawDfmFinding[];
  geometry_report: Record<string, unknown>;
  decision_json: RawDecisionJson;
}
