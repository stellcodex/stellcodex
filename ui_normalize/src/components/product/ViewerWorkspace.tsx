"use client";

import * as React from "react";

import { Card } from "@/components/primitives/Card";
import { ShareDialog } from "@/components/shares/ShareDialog";
import { RouteErrorState } from "@/components/states/RouteErrorState";
import { RouteLoadingState } from "@/components/states/RouteLoadingState";
import type { ViewerNodeRecord } from "@/lib/contracts/ui";
import { useDecision } from "@/lib/hooks/useDecision";
import { useDfmReport } from "@/lib/hooks/useDfmReport";
import { usePolling } from "@/lib/hooks/usePolling";
import { useRequiredInputs } from "@/lib/hooks/useRequiredInputs";
import { useShares } from "@/lib/hooks/useShares";
import { useViewerData } from "@/lib/hooks/useViewerData";
import { useViewerStore } from "@/lib/stores/viewerStore";

import { AssemblyTree } from "../viewer/AssemblyTree";
import { SelectionInfo } from "../viewer/SelectionInfo";
import { TreeSearch } from "../viewer/TreeSearch";
import { ViewerCanvas } from "../viewer/ViewerCanvas";
import { ViewerToolbar } from "../viewer/ViewerToolbar";
import { ViewerIntelligencePanel } from "./ViewerIntelligencePanel";

export interface ViewerWorkspaceProps {
  fileId: string;
}

function filterNodes(query: string, nodes: ViewerNodeRecord[]) {
  if (!query.trim()) return nodes;
  const token = query.trim().toLowerCase();
  return nodes
    .map((node) => {
      const children = filterNodes(token, node.children);
      const matches = node.label.toLowerCase().includes(token) || node.occurrenceId.toLowerCase().includes(token);
      if (matches || children.length > 0) return { ...node, children };
      return null;
    })
    .filter((node): node is NonNullable<typeof node> => Boolean(node));
}

export function ViewerWorkspace({ fileId }: ViewerWorkspaceProps) {
  const { viewer, loading, error, refresh } = useViewerData(fileId);
  const { decision, error: decisionError, refresh: refreshDecision } = useDecision({ fileId });
  const { report, error: dfmError, refresh: refreshDfm, rerunSupported } = useDfmReport(fileId);
  const { fields, values, error: inputsError, setValue, submit } = useRequiredInputs(decision?.sessionId ?? null);
  const { create } = useShares(fileId);
  const {
    hiddenNodeIds,
    isolatedNodeId,
    resetVisibility,
    searchQuery,
    selectedNodeIds,
    setIsolatedNodeId,
    setSearchQuery,
    setSelectedNodeIds,
    toggleHiddenNode,
  } = useViewerStore();
  const [shareDialogOpen, setShareDialogOpen] = React.useState(false);
  const [fitSequence, setFitSequence] = React.useState(0);
  const [fitMode, setFitMode] = React.useState<"model" | "selection" | "reset" | null>(null);
  const containerRef = React.useRef<HTMLDivElement | null>(null);

  React.useEffect(() => {
    setSelectedNodeIds([]);
    setIsolatedNodeId(null);
    setSearchQuery("");
    resetVisibility();
  }, [fileId, resetVisibility, setIsolatedNodeId, setSearchQuery, setSelectedNodeIds]);

  usePolling({
    enabled: Boolean(viewer && viewer.state === "processing"),
    intervalMs: 5000,
    callback: async () => {
      await Promise.all([refresh(), refreshDecision(), refreshDfm()]);
    },
  });

  if (loading) return <RouteLoadingState title="Loading viewer workspace" />;
  if (error || !viewer) return <RouteErrorState actionLabel="Retry" description={error || "Viewer data unavailable."} onAction={() => void refresh()} title="Viewer unavailable" />;

  const filteredNodes = filterNodes(searchQuery, viewer.nodes);

  return (
    <div className="flex h-full min-h-0 flex-col overflow-hidden rounded-[12px] border border-[#eeeeee] bg-white" ref={containerRef}>
      <ViewerToolbar
        file={viewer.file}
        onFitModel={() => {
          setFitMode("model");
          setFitSequence((value) => value + 1);
        }}
        onFitSelection={() => {
          setFitMode("selection");
          setFitSequence((value) => value + 1);
        }}
        onOpenShare={() => setShareDialogOpen(true)}
        onResetView={() => {
          resetVisibility();
          setSelectedNodeIds([]);
          setFitMode("reset");
          setFitSequence((value) => value + 1);
        }}
        onToggleFullscreen={() => {
          if (!containerRef.current) return;
          if (document.fullscreenElement) {
            void document.exitFullscreen();
          } else {
            void containerRef.current.requestFullscreen();
          }
        }}
      />

      <div className="min-h-0 flex-1 overflow-x-auto">
        <div className="grid min-h-full min-w-[1240px] grid-cols-[320px_minmax(0,1fr)_420px]">
          <aside className="min-h-0 border-r border-[#eeeeee] bg-white">
            <div className="flex h-full min-h-0 flex-col gap-4 px-4 py-4">
              <Card title="Assembly">
                <div className="space-y-3 text-sm">
                  <div className="flex justify-between gap-3">
                    <span className="text-[var(--foreground-soft)]">Occurrences</span>
                    <span className="font-medium text-[var(--foreground-strong)]">{viewer.occurrenceCount}</span>
                  </div>
                  <div className="flex justify-between gap-3">
                    <span className="text-[var(--foreground-soft)]">Model state</span>
                    <span className="font-medium text-[var(--foreground-strong)]">{viewer.state}</span>
                  </div>
                </div>
              </Card>
              <TreeSearch onChange={setSearchQuery} value={searchQuery} />
              <SelectionInfo hiddenCount={hiddenNodeIds.length} isolatedNodeId={isolatedNodeId} selectedCount={selectedNodeIds.length} />
              <div className="min-h-0 flex-1">
                <AssemblyTree
                  hiddenIds={hiddenNodeIds}
                  isolatedNodeId={isolatedNodeId}
                  nodes={filteredNodes}
                  onHide={toggleHiddenNode}
                  onIsolate={(nodeId) => setIsolatedNodeId(isolatedNodeId === nodeId ? null : nodeId)}
                  onReset={resetVisibility}
                  onSelect={(nodeId) => setSelectedNodeIds([nodeId])}
                  selectedIds={selectedNodeIds}
                />
              </div>
            </div>
          </aside>

          <section className="min-h-0 bg-white p-4">
            <ViewerCanvas
              fitMode={fitMode}
              fitSequence={fitSequence}
              hiddenOccurrenceIds={hiddenNodeIds}
              isolatedOccurrenceId={isolatedNodeId}
              onSelectOccurrence={(occurrenceId) => setSelectedNodeIds([occurrenceId])}
              selectedOccurrenceIds={selectedNodeIds}
              viewer={viewer}
            />
          </section>

          <aside className="min-h-0 overflow-y-auto border-l border-[#eeeeee] bg-white px-4 py-4">
            <ViewerIntelligencePanel
              decision={decision}
              decisionError={decisionError}
              dfm={report}
              dfmError={dfmError}
              fields={fields}
              fileStateMessage={viewer.stateMessage}
              inputsError={inputsError}
              onChange={setValue}
              onSubmit={submit}
              rerunSupported={rerunSupported}
              values={values}
            />
          </aside>
        </div>
      </div>

      <ShareDialog
        onClose={() => setShareDialogOpen(false)}
        onCreate={async (permission, expiresInSeconds) => {
          await create(viewer.file.fileId, permission, expiresInSeconds);
        }}
        open={shareDialogOpen}
      />
    </div>
  );
}
