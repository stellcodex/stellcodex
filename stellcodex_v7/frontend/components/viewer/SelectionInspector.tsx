import type { ViewerOccurrenceNode } from "@/lib/contracts/viewer";
import { Panel } from "@/components/primitives/Panel";

export interface SelectionInspectorProps {
  selectedNode: ViewerOccurrenceNode | null;
}

export function SelectionInspector({ selectedNode }: SelectionInspectorProps) {
  return (
    <Panel title="Selection">
      {selectedNode ? (
        <dl className="sc-kv">
          <dt>Label</dt>
          <dd>{selectedNode.label}</dd>
          <dt>Path</dt>
          <dd>{selectedNode.occurrencePath}</dd>
          <dt>Children</dt>
          <dd>{selectedNode.childCount || 0}</dd>
        </dl>
      ) : (
        <span className="sc-muted">No occurrence selected</span>
      )}
    </Panel>
  );
}
