import type { FileSummary } from "@/lib/contracts/files";
import { Panel } from "@/components/primitives/Panel";

export function AttentionPanel({ items }: { items: FileSummary[] }) {
  return (
    <Panel title="Attention">
      <div className="sc-stack">
        {items.length > 0 ? (
          items.map((item) => (
            <div key={item.fileId} className="sc-inline" style={{ justifyContent: "space-between" }}>
              <span>{item.fileName}</span>
              <span className="sc-muted">{item.status}</span>
            </div>
          ))
        ) : (
          <span className="sc-muted">No immediate issues detected.</span>
        )}
      </div>
    </Panel>
  );
}
