import { Card } from "@/components/primitives/Card";
import type { DecisionRecord, DfmRecord, RequiredInputRecord } from "@/lib/contracts/ui";

import { ActivityEvidencePanel } from "../intelligence/ActivityEvidencePanel";
import { ApprovalPanel } from "../intelligence/ApprovalPanel";
import { DecisionPanel } from "../intelligence/DecisionPanel";
import { DfmReportPanel } from "../intelligence/DfmReportPanel";
import { RequiredInputsPanel } from "../intelligence/RequiredInputsPanel";
import { RisksPanel } from "../intelligence/RisksPanel";
import { StatePanel } from "../intelligence/StatePanel";

export interface ViewerIntelligencePanelProps {
  decision: DecisionRecord | null;
  decisionError: string | null;
  dfm: DfmRecord | null;
  dfmError: string | null;
  fields: RequiredInputRecord[];
  fileCreatedAt: string;
  fileStateMessage: string;
  fileStatus: string;
  inputsError: string | null;
  onApprove: (reason?: string) => Promise<void>;
  onChange: (key: string, value: string) => void;
  onReject: (reason?: string) => Promise<void>;
  onSubmit: () => Promise<boolean>;
  rerunSupported: boolean;
  shareCount: number;
  values: Record<string, string>;
}

export function ViewerIntelligencePanel({
  decision,
  decisionError,
  dfm,
  dfmError,
  fields,
  fileCreatedAt,
  fileStateMessage,
  fileStatus,
  inputsError,
  onApprove,
  onChange,
  onReject,
  onSubmit,
  rerunSupported,
  shareCount,
  values,
}: ViewerIntelligencePanelProps) {
  const hasStatus = Boolean(fileStateMessage || decisionError || dfmError);

  return (
    <div className="space-y-4">
      {hasStatus ? (
        <Card title="Status">
          <div className="space-y-2 text-sm text-[var(--foreground-muted)]">
            {fileStateMessage ? <div>{fileStateMessage}</div> : null}
            {decisionError ? <div>{decisionError}</div> : null}
            {dfmError ? <div>{dfmError}</div> : null}
          </div>
        </Card>
      ) : null}
      <StatePanel decision={decision} />
      <RequiredInputsPanel error={inputsError} fields={fields} onChange={onChange} onSubmit={onSubmit} values={values} />
      <DecisionPanel decision={decision} />
      <RisksPanel decision={decision} dfm={dfm} />
      <DfmReportPanel report={dfm} rerunSupported={rerunSupported} />
      <ActivityEvidencePanel createdAt={fileCreatedAt} shareCount={shareCount} status={fileStatus} />
      <ApprovalPanel decision={decision} onApprove={onApprove} onReject={onReject} />
    </div>
  );
}
