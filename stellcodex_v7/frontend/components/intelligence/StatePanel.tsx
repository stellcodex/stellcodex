import type { OrchestratorStateSummary } from "@/lib/contracts/orchestrator";
import { Button } from "@/components/primitives/Button";
import { Panel } from "@/components/primitives/Panel";
import { ApprovalStatusBadge } from "@/components/status/ApprovalStatusBadge";
import { OrchestratorStateBadge } from "@/components/status/OrchestratorStateBadge";

export interface StatePanelProps {
  state: OrchestratorStateSummary | null;
  onRefresh: () => void;
  onAdvance?: () => void;
}

export function StatePanel({ state, onRefresh, onAdvance }: StatePanelProps) {
  return (
    <Panel
      title="Workflow state"
      actions={
        <div className="sc-inline">
          <Button variant="ghost" onClick={onRefresh}>
            Refresh
          </Button>
          {onAdvance ? <Button variant="ghost" onClick={onAdvance}>Advance</Button> : null}
        </div>
      }
    >
      {state ? (
        <div className="sc-stack">
          <div className="sc-inline">
            <OrchestratorStateBadge stateCode={state.stateCode} stateLabel={state.stateLabel} />
            <ApprovalStatusBadge status={state.approvalRequired ? "required" : "clear"} />
          </div>
          {state.blockedReason ? <span className="sc-muted">{state.blockedReason}</span> : null}
          {state.progressLabel ? <span className="sc-muted">{state.progressLabel}</span> : null}
        </div>
      ) : (
        <span className="sc-muted">Decision not available yet</span>
      )}
    </Panel>
  );
}
