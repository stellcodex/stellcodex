import { EmptyState } from "@/components/primitives/EmptyState";
import { Panel } from "@/components/primitives/Panel";
import type { DecisionRecord } from "@/lib/contracts/ui";

export interface DecisionPanelProps {
  decision: DecisionRecord | null;
}

export function DecisionPanel({ decision }: DecisionPanelProps) {
  return (
    <Panel title="Decision">
      {!decision ? (
        <EmptyState description="No decision payload is available for this file." title="Decision unavailable" />
      ) : (
        <div className="space-y-4 text-sm">
          <dl className="grid gap-3 md:grid-cols-2">
            <div>
              <dt className="text-[var(--foreground-soft)]">Manufacturing method</dt>
              <dd className="mt-1 font-medium">{decision.manufacturingMethod}</dd>
            </div>
            <div>
              <dt className="text-[var(--foreground-soft)]">Mode</dt>
              <dd className="mt-1 font-medium">{decision.mode}</dd>
            </div>
            <div>
              <dt className="text-[var(--foreground-soft)]">Confidence</dt>
              <dd className="mt-1 font-medium">{decision.confidence.toFixed(3)}</dd>
            </div>
            <div>
              <dt className="text-[var(--foreground-soft)]">Rule version</dt>
              <dd className="mt-1 font-medium">{decision.ruleVersion}</dd>
            </div>
          </dl>
          <div className="space-y-2">
            <div className="text-sm font-medium text-[var(--foreground-strong)]">Rule explanations</div>
            {decision.explanations.map((item) => (
              <div key={item.ruleId} className="rounded-[12px] border border-[#eeeeee] px-3 py-3">
                <div className="text-sm font-medium">{item.ruleId}</div>
                <div className="mt-1 text-sm text-[var(--foreground-muted)]">{item.reference}</div>
                <div className="mt-2 text-sm">{item.reasoning}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </Panel>
  );
}
