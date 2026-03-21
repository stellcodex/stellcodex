"use client";

import * as React from "react";

import { Button } from "@/components/primitives/Button";
import { EmptyState } from "@/components/primitives/EmptyState";
import { Input } from "@/components/primitives/Input";
import { Panel } from "@/components/primitives/Panel";
import type { DecisionRecord } from "@/lib/contracts/ui";

export interface ApprovalPanelProps {
  decision: DecisionRecord | null;
  onApprove: (reason?: string) => Promise<void>;
  onReject: (reason?: string) => Promise<void>;
}

export function ApprovalPanel({ decision, onApprove, onReject }: ApprovalPanelProps) {
  const [reason, setReason] = React.useState("");
  const [busy, setBusy] = React.useState<"approve" | "reject" | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  if (!decision?.approvalRequired) {
    return <Panel title="Approval"><EmptyState description="Approval actions are not currently required for this file." title="No approval required" /></Panel>;
  }

  async function handleAction(action: "approve" | "reject") {
    setBusy(action);
    setError(null);
    try {
      if (action === "approve") {
        await onApprove(reason);
      } else {
        await onReject(reason);
      }
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Approval action failed.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <Panel description="Approval actions are shown only when the backend session marks approval_required." title="Approval">
      <div className="space-y-4">
        <Input onChange={(event) => setReason(event.target.value)} placeholder="Reason" value={reason} />
        {error ? <div className="text-sm text-[var(--status-danger-fg)]">{error}</div> : null}
        <div className="flex gap-3">
          <Button onClick={() => void handleAction("approve")} variant="primary">
            {busy === "approve" ? "Approving..." : "Approve"}
          </Button>
          <Button onClick={() => void handleAction("reject")} variant="danger">
            {busy === "reject" ? "Rejecting..." : "Reject"}
          </Button>
        </div>
      </div>
    </Panel>
  );
}
