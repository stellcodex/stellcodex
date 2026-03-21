import { Panel } from "@/components/primitives/Panel";
import type { DecisionRecord } from "@/lib/contracts/ui";

import { FileStatusBadge } from "../files/FileStatusBadge";

export interface StatePanelProps {
  decision: DecisionRecord | null;
}

export function StatePanel({ decision }: StatePanelProps) {
  return (
    <Panel description="The current orchestrator state is rendered from the backend session." title="State">
      <div className="space-y-3 text-sm">
        <div className="flex justify-between">
          <span className="text-[var(--foreground-soft)]">State code</span>
          <span className="font-medium">{decision?.stateCode || "Unavailable"}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-[var(--foreground-soft)]">Label</span>
          <span className="font-medium">{decision?.stateLabel || "Unavailable"}</span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-[var(--foreground-soft)]">Approval</span>
          <FileStatusBadge status={decision?.approvalRequired ? "awaiting approval" : "pass"} />
        </div>
      </div>
    </Panel>
  );
}
