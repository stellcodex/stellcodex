"use client";

import type { ViewerOccurrenceNode } from "@/lib/contracts/viewer";
import { Button } from "@/components/primitives/Button";

export interface AssemblyTreeNodeProps {
  node: ViewerOccurrenceNode;
  depth?: number;
  onSelect: (node: ViewerOccurrenceNode) => void;
}

export function AssemblyTreeNode({ node, depth = 0, onSelect }: AssemblyTreeNodeProps) {
  return (
    <div className="sc-stack" style={{ paddingLeft: `${depth * 12}px` }}>
      <Button variant="ghost" onClick={() => onSelect(node)} className="sc-tree-row" data-selected={node.selected ? "true" : "false"}>
        <span>{node.label}</span>
        <span className="sc-muted">{node.childCount || 0}</span>
      </Button>
      {(node.children || []).map((child) => (
        <AssemblyTreeNode key={child.nodeId} node={child} depth={depth + 1} onSelect={onSelect} />
      ))}
    </div>
  );
}
