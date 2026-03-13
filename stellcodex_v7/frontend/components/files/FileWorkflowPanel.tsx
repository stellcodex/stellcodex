import type { OrchestratorStateSummary } from "@/lib/contracts/orchestrator";
import { Panel } from "@/components/primitives/Panel";
import { OrchestratorStateBadge } from "@/components/status/OrchestratorStateBadge";
import { ApprovalStatusBadge } from "@/components/status/ApprovalStatusBadge";

export interface FileWorkflowPanelProps {
  workflow: OrchestratorStateSummary | null;
}

export function FileWorkflowPanel({ workflow }: FileWorkflowPanelProps) {
  return (
    <Panel title="Workflow">
      {workflow ? (
        <div className="sc-stack">
          <div className="sc-inline">
            <OrchestratorStateBadge stateCode={workflow.stateCode} stateLabel={workflow.stateLabel} />
            <ApprovalStatusBadge status={workflow.approvalRequired ? "required" : "not_required"} />
          </div>
          {workflow.blockedReason ? <span className="sc-muted">{workflow.blockedReason}</span> : null}
        </div>
      ) : (
        <span className="sc-muted">Decision not available yet</span>
      )}
    </Panel>
  );
}
