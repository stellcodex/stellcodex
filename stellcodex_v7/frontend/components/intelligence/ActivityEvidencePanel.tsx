import { Panel } from "@/components/primitives/Panel";

export type ActivityEvidenceItem = {
  id: string;
  timestamp?: string | null;
  description: string;
};

export interface ActivityEvidencePanelProps {
  items: ActivityEvidenceItem[];
}

export function ActivityEvidencePanel({ items }: ActivityEvidencePanelProps) {
  return (
    <Panel title="Activity and evidence">
      <div className="sc-stack">
        {items.length > 0 ? (
          items.map((item) => (
            <div key={item.id} className="sc-inline" style={{ justifyContent: "space-between" }}>
              <span>{item.description}</span>
              <span className="sc-muted">{item.timestamp || "No timestamp"}</span>
            </div>
          ))
        ) : (
          <span className="sc-muted">No activity yet</span>
        )}
      </div>
    </Panel>
  );
}
