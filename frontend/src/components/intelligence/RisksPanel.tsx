import { EmptyState } from "@/components/primitives/EmptyState";
import { Panel } from "@/components/primitives/Panel";
import type { DecisionRecord, DfmRecord } from "@/lib/contracts/ui";

export interface RisksPanelProps {
  decision: DecisionRecord | null;
  dfm: DfmRecord | null;
}

export function RisksPanel({ decision, dfm }: RisksPanelProps) {
  const rows = [
    ...(decision?.riskFlags.map((flag) => ({ code: flag, severity: "HIGH", message: flag, recommendation: null })) ?? []),
    ...(dfm?.findings.map((finding) => ({
      code: finding.code,
      severity: finding.severity,
      message: finding.message,
      recommendation: finding.recommendation,
    })) ?? []),
  ];

  return (
    <Panel description="Risk flags and DFM findings are surfaced without placeholder data." title="Risks">
      {rows.length === 0 ? (
        <EmptyState description="No risks were returned by the current decision or DFM payloads." title="No risks" />
      ) : (
        <div className="space-y-3">
          {rows.map((row) => (
            <div key={`${row.code}-${row.message}`} className="rounded-[var(--radius-md)] border border-[var(--border-muted)] px-3 py-3">
              <div className="text-sm font-medium">{row.code}</div>
              <div className="mt-1 text-xs uppercase tracking-[0.12em] text-[var(--foreground-soft)]">{row.severity}</div>
              <div className="mt-2 text-sm text-[var(--foreground-default)]">{row.message}</div>
              {row.recommendation ? <div className="mt-2 text-xs text-[var(--foreground-muted)]">{row.recommendation}</div> : null}
            </div>
          ))}
        </div>
      )}
    </Panel>
  );
}
