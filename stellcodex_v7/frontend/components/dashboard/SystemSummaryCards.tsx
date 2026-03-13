import { Panel } from "@/components/primitives/Panel";

type SystemSummaryCardsProps = {
  filesCount: number;
  processingCount: number;
  failedCount: number;
  healthLabel: string;
};

export function SystemSummaryCards({ filesCount, processingCount, failedCount, healthLabel }: SystemSummaryCardsProps) {
  return (
    <div className="sc-grid sc-grid-2">
      <Panel title="Files">
        <div className="sc-stack">
          <strong>{filesCount}</strong>
          <span className="sc-muted">Visible files</span>
        </div>
      </Panel>
      <Panel title="Processing">
        <div className="sc-stack">
          <strong>{processingCount}</strong>
          <span className="sc-muted">Queued or running</span>
        </div>
      </Panel>
      <Panel title="Failed">
        <div className="sc-stack">
          <strong>{failedCount}</strong>
          <span className="sc-muted">Files needing attention</span>
        </div>
      </Panel>
      <Panel title="Health">
        <div className="sc-stack">
          <strong>{healthLabel}</strong>
          <span className="sc-muted">API health state</span>
        </div>
      </Panel>
    </div>
  );
}
