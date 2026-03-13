"use client";

import type { ViewerOccurrenceNode } from "@/lib/contracts/viewer";
import { Panel } from "@/components/primitives/Panel";
import { ScrollArea } from "@/components/primitives/ScrollArea";
import { AssemblyTreeNode } from "@/components/viewer/AssemblyTreeNode";
import { TreeSearch } from "@/components/viewer/TreeSearch";
import { VisibilityControls } from "@/components/viewer/VisibilityControls";

export interface AssemblyTreeProps {
  nodes: ViewerOccurrenceNode[];
  searchQuery: string;
  onSearchChange: (value: string) => void;
  onSelect: (node: ViewerOccurrenceNode) => void;
  onShowAll: () => void;
  onHideSelected: () => void;
  disableShowAll?: boolean;
  disableHide?: boolean;
  visibilityHint?: string;
}

export function AssemblyTree({
  nodes,
  searchQuery,
  onSearchChange,
  onSelect,
  onShowAll,
  onHideSelected,
  disableShowAll = false,
  disableHide = false,
  visibilityHint,
}: AssemblyTreeProps) {
  return (
    <Panel
      title="Assembly tree"
      actions={
        <VisibilityControls
          onShowAll={onShowAll}
          onHideSelected={onHideSelected}
          disableShowAll={disableShowAll}
          disableHide={disableHide}
          hint={visibilityHint}
        />
      }
    >
      <div className="sc-stack">
        <TreeSearch value={searchQuery} onChange={onSearchChange} />
        <ScrollArea className="sc-tree">
          {nodes.map((node) => (
            <AssemblyTreeNode key={node.nodeId} node={node} onSelect={onSelect} />
          ))}
          {nodes.length === 0 ? <span className="sc-muted">Viewer unavailable: assembly metadata missing</span> : null}
        </ScrollArea>
      </div>
    </Panel>
  );
}
