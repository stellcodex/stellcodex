import type { DecisionSummary, OrchestratorStateSummary, RequiredInputField } from "@/lib/contracts/orchestrator";
import type { DfmReportSummary, RiskSummary } from "@/lib/contracts/dfm";
import { ActivityEvidencePanel, type ActivityEvidenceItem } from "@/components/intelligence/ActivityEvidencePanel";
import { ApprovalPanel } from "@/components/intelligence/ApprovalPanel";
import { DecisionPanel } from "@/components/intelligence/DecisionPanel";
import { DfmReportPanel } from "@/components/intelligence/DfmReportPanel";
import { RequiredInputsPanel } from "@/components/intelligence/RequiredInputsPanel";
import { RisksPanel } from "@/components/intelligence/RisksPanel";
import { StatePanel } from "@/components/intelligence/StatePanel";

export interface IntelligencePanelProps {
  state: OrchestratorStateSummary | null;
  decision: DecisionSummary | null;
  fields: RequiredInputField[];
  risks: RiskSummary[];
  report: DfmReportSummary | null;
  activity: ActivityEvidenceItem[];
  onRefresh: () => void;
  onAdvance?: () => void;
  onFieldChange: (key: string, value: RequiredInputField["value"]) => void;
  onSubmitInputs: () => void;
  onApprove?: () => void;
  onReject?: () => void;
  onRerunDfm: () => void;
  approvalBusy?: boolean;
  dfmBusy?: boolean;
}

export function IntelligencePanel({
  state,
  decision,
  fields,
  risks,
  report,
  activity,
  onRefresh,
  onAdvance,
  onFieldChange,
  onSubmitInputs,
  onApprove,
  onReject,
  onRerunDfm,
  approvalBusy = false,
  dfmBusy = false,
}: IntelligencePanelProps) {
  return (
    <div className="sc-stack">
      <StatePanel state={state} onRefresh={onRefresh} onAdvance={onAdvance} />
      <RequiredInputsPanel fields={fields} onChange={onFieldChange} onSubmit={onSubmitInputs} />
      <DecisionPanel decision={decision} />
      <RisksPanel risks={risks} />
      <DfmReportPanel report={report} onRerun={onRerunDfm} running={dfmBusy} />
      <ActivityEvidencePanel items={activity} />
      <ApprovalPanel approvalRequired={Boolean(state?.approvalRequired)} onApprove={onApprove} onReject={onReject} busy={approvalBusy} />
    </div>
  );
}
