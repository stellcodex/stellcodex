"use client";

import * as React from "react";

import { Button } from "@/components/primitives/Button";
import { ScrollArea } from "@/components/primitives/ScrollArea";
import type { ViewerNodeRecord } from "@/lib/contracts/ui";

export interface AssemblyTreeProps {
  nodes: ViewerNodeRecord[];
  selectedIds: string[];
  hiddenIds: string[];
  isolatedNodeId: string | null;
  onSelect: (nodeId: string) => void;
  onHide: (nodeId: string) => void;
  onIsolate: (nodeId: string) => void;
  onReset: () => void;
}

function TreeNode({
  node,
  selectedIds,
  hiddenIds,
  isolatedNodeId,
  onSelect,
  onHide,
  onIsolate,
}: {
  node: ViewerNodeRecord;
  selectedIds: string[];
  hiddenIds: string[];
  isolatedNodeId: string | null;
  onSelect: (nodeId: string) => void;
  onHide: (nodeId: string) => void;
  onIsolate: (nodeId: string) => void;
}) {
  const selected = selectedIds.includes(node.occurrenceId);
  const hidden = hiddenIds.includes(node.occurrenceId);
  const isolated = isolatedNodeId === node.occurrenceId;

  return (
    <div className="space-y-2">
      <div className="rounded-[var(--radius-md)] border border-[var(--border-muted)] px-3 py-3">
        <div className="flex items-start justify-between gap-3">
          <button className="text-left" onClick={() => onSelect(node.occurrenceId)} type="button">
            <div className="text-sm font-medium text-[var(--foreground-strong)]">{node.label}</div>
            <div className="text-xs text-[var(--foreground-muted)]">
              {node.occurrenceId} · {node.kind} · qty {Math.max(node.partCount, 1)}
            </div>
          </button>
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => onSelect(node.occurrenceId)} size="sm" variant={selected ? "primary" : "secondary"}>
              Select
            </Button>
            <Button onClick={() => onHide(node.occurrenceId)} size="sm">
              {hidden ? "Show" : "Hide"}
            </Button>
            <Button onClick={() => onIsolate(node.occurrenceId)} size="sm" variant={isolated ? "primary" : "secondary"}>
              Isolate
            </Button>
          </div>
        </div>
      </div>
      {node.children.length > 0 ? (
        <div className="ml-4 space-y-2 border-l border-[var(--border-muted)] pl-3">
          {node.children.map((child) => (
            <TreeNode
              hiddenIds={hiddenIds}
              isolatedNodeId={isolatedNodeId}
              key={child.occurrenceId}
              node={child}
              onHide={onHide}
              onIsolate={onIsolate}
              onSelect={onSelect}
              selectedIds={selectedIds}
            />
          ))}
        </div>
      ) : null}
    </div>
  );
}

export function AssemblyTree({
  hiddenIds,
  isolatedNodeId,
  nodes,
  onHide,
  onIsolate,
  onReset,
  onSelect,
  selectedIds,
}: AssemblyTreeProps) {
  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div className="text-xs font-semibold uppercase tracking-[0.16em] text-[var(--foreground-soft)]">Assembly tree</div>
        <Button onClick={onReset} size="sm">
          Reset
        </Button>
      </div>
      <ScrollArea className="max-h-[calc(100vh-18rem)] space-y-2 pr-2">
        <div className="space-y-2">
          {nodes.map((node) => (
            <TreeNode
              hiddenIds={hiddenIds}
              isolatedNodeId={isolatedNodeId}
              key={node.occurrenceId}
              node={node}
              onHide={onHide}
              onIsolate={onIsolate}
              onSelect={onSelect}
              selectedIds={selectedIds}
            />
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
