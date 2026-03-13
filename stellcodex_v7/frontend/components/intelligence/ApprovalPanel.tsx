"use client";

import { Button } from "@/components/primitives/Button";
import { Panel } from "@/components/primitives/Panel";
import { ApprovalStatusBadge } from "@/components/status/ApprovalStatusBadge";

export interface ApprovalPanelProps {
  approvalRequired: boolean;
  onApprove?: () => void;
  onReject?: () => void;
  busy?: boolean;
}

export function ApprovalPanel({ approvalRequired, onApprove, onReject, busy = false }: ApprovalPanelProps) {
  return (
    <Panel title="Approval">
      <div className="sc-stack">
        <ApprovalStatusBadge status={approvalRequired ? "required" : "clear"} />
        {approvalRequired ? (
          <div className="sc-inline">
            <Button variant="primary" onClick={onApprove} loading={busy} disabled={!onApprove}>
              Approve
            </Button>
            <Button variant="danger" onClick={onReject} disabled={!onReject || busy}>
              Reject
            </Button>
          </div>
        ) : (
          <span className="sc-muted">No approval required</span>
        )}
      </div>
    </Panel>
  );
}
