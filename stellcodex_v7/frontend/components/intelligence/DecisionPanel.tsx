import type { DecisionSummary } from "@/lib/contracts/orchestrator";
import { Panel } from "@/components/primitives/Panel";

export interface DecisionPanelProps {
  decision: DecisionSummary | null;
}

export function DecisionPanel({ decision }: DecisionPanelProps) {
  return (
    <Panel title="Decision">
      {decision ? (
        <dl className="sc-kv">
          <dt>Manufacturing method</dt>
          <dd>{decision.manufacturingMethod || "Not available"}</dd>
          <dt>Mode</dt>
          <dd>{decision.mode || "Not available"}</dd>
          <dt>Confidence</dt>
          <dd>{decision.confidence == null ? "Not available" : decision.confidence.toFixed(2)}</dd>
          <dt>Rule version</dt>
          <dd>{decision.ruleVersion || "Not available"}</dd>
        </dl>
      ) : (
        <span className="sc-muted">Decision not available yet</span>
      )}
    </Panel>
  );
}
