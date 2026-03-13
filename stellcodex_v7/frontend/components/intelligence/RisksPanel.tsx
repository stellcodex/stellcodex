import type { RiskSummary } from "@/lib/contracts/dfm";
import { Panel } from "@/components/primitives/Panel";
import { RiskSeverityBadge } from "@/components/status/RiskSeverityBadge";

export interface RisksPanelProps {
  risks: RiskSummary[];
}

export function RisksPanel({ risks }: RisksPanelProps) {
  return (
    <Panel title="Risks">
      <div className="sc-stack">
        {risks.length > 0 ? (
          risks.map((risk) => (
            <div key={risk.id} className="sc-stack">
              <div className="sc-inline">
                <RiskSeverityBadge severity={risk.severity} />
                <strong>{risk.title}</strong>
              </div>
              {risk.description ? <span className="sc-muted">{risk.description}</span> : null}
            </div>
          ))
        ) : (
          <span className="sc-muted">No risks detected</span>
        )}
      </div>
    </Panel>
  );
}
