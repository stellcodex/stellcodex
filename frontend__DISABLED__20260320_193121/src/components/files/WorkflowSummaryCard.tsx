import { Card } from "@/components/primitives/Card";
import type { DecisionRecord, DfmRecord } from "@/lib/contracts/ui";

import { FileStatusBadge } from "./FileStatusBadge";

export interface WorkflowSummaryCardProps {
  status: string;
  decision: DecisionRecord | null;
  dfm: DfmRecord | null;
  shareCount: number;
}

export function WorkflowSummaryCard({ decision, dfm, shareCount, status }: WorkflowSummaryCardProps) {
  return (
    <Card description="Real workflow status derived from backend state, decision, DFM, and share records." title="Workflow summary">
      <div className="grid gap-4 text-sm md:grid-cols-4">
        <div>
          <div className="text-[var(--foreground-soft)]">File status</div>
          <div className="mt-1">
            <FileStatusBadge status={status} />
          </div>
        </div>
        <div>
          <div className="text-[var(--foreground-soft)]">Orchestrator state</div>
          <div className="mt-1 font-medium">{decision?.stateCode || "Unavailable"}</div>
        </div>
        <div>
          <div className="text-[var(--foreground-soft)]">DFM gate</div>
          <div className="mt-1 font-medium">{dfm?.statusGate || "Not generated"}</div>
        </div>
        <div>
          <div className="text-[var(--foreground-soft)]">Shares</div>
          <div className="mt-1 font-medium">{shareCount}</div>
        </div>
      </div>
    </Card>
  );
}
