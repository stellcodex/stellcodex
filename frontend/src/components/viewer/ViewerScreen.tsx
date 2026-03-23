"use client";

import * as React from "react";

import { Tabs } from "@/components/primitives/Tabs";
import { Card } from "@/components/primitives/Card";
import { ShareDialog } from "@/components/shares/ShareDialog";
import { RouteErrorState } from "@/components/states/RouteErrorState";
import { RouteLoadingState } from "@/components/states/RouteLoadingState";
import { useDecision } from "@/lib/hooks/useDecision";
import { useDfmReport } from "@/lib/hooks/useDfmReport";
import { usePolling } from "@/lib/hooks/usePolling";
import { useRequiredInputs } from "@/lib/hooks/useRequiredInputs";
import { useShares } from "@/lib/hooks/useShares";
import { useViewerData } from "@/lib/hooks/useViewerData";
import { approveSession, rejectSession } from "@/lib/api/orchestrator";
import { useViewerStore } from "@/lib/stores/viewerStore";
import type { ViewerNodeRecord } from "@/lib/contracts/ui";

import { ActivityEvidencePanel } from "../intelligence/ActivityEvidencePanel";
import { ApprovalPanel } from "../intelligence/ApprovalPanel";
import { DecisionPanel } from "../intelligence/DecisionPanel";
import { DfmReportPanel } from "../intelligence/DfmReportPanel";
import { RequiredInputsPanel } from "../intelligence/RequiredInputsPanel";
import { RisksPanel } from "../intelligence/RisksPanel";
import { StatePanel } from "../intelligence/StatePanel";
import { AssemblyTree } from "./AssemblyTree";
import { SelectionInfo } from "./SelectionInfo";
import { TreeSearch } from "./TreeSearch";
import { ViewerCanvas } from "./ViewerCanvas";
import { ViewerToolbar } from "./ViewerToolbar";

export interface ViewerScreenProps {
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

export function ViewerScreen({ fileId }: ViewerScreenProps) {
  const { viewer, loading, error, refresh } = useViewerData(fileId);
  const { decision, refresh: refreshDecision } = useDecision({ fileId });
  const { report, refresh: refreshDfm, rerunSupported } = useDfmReport(fileId);
  const { fields, values, error: inputsError, setValue, submit } = useRequiredInputs(decision?.sessionId ?? null);
  const { create, shares } = useShares(fileId);
  const {
    hiddenNodeIds,
    isolatedNodeId,
    resetVisibility,
    searchQuery,
    selectedNodeIds,
    setSearchQuery,
    setSelectedNodeIds,
    toggleHiddenNode,
  } = useViewerStore();
  const [shareDialogOpen, setShareDialogOpen] = React.useState(false);
  const [fitSequence, setFitSequence] = React.useState(0);
  const [fitMode, setFitMode] = React.useState<"model" | "selection" | "reset" | null>(null);
  const containerRef = React.useRef<HTMLDivElement | null>(null);

  usePolling({
    enabled: Boolean(viewer && viewer.state === "processing"),
    intervalMs: 5000,
    callback: async () => {
      await Promise.all([refresh(), refreshDecision(), refreshDfm()]);
    },
  });

  if (loading) return <RouteLoadingState title="Loading viewer workstation" />;
  if (error || !viewer) return <RouteErrorState actionLabel="Retry" description={error || "Viewer data unavailable."} onAction={() => void refresh()} title="Viewer unavailable" />;

  const filteredNodes = filterNodes(searchQuery, viewer.nodes);

  async function handleApproval(action: "approve" | "reject", reason?: string) {
    if (!decision?.sessionId) return;
    if (action === "approve") {
      await approveSession(decision.sessionId, reason);
    } else {
      await rejectSession(decision.sessionId, reason);
    }
    await refreshDecision();
  }

  async function handleSubmitInputs() {
    const accepted = await submit();
    if (accepted) {
      await Promise.all([refresh(), refreshDecision(), refreshDfm()]);
    }
    return accepted;
  }

  return (
    <div className="space-y-0 overflow-hidden rounded-[var(--radius-xl)] border border-[var(--border-default)] bg-[var(--background-shell)]" ref={containerRef}>
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
      <div className="grid min-h-[calc(100vh-13rem)] grid-cols-[320px_minmax(0,1fr)_420px]">
        <aside className="border-r border-[var(--border-muted)] bg-[var(--background-surface)] px-4 py-4">
          <div className="space-y-4">
            <TreeSearch onChange={setSearchQuery} value={searchQuery} />
            <SelectionInfo hiddenCount={hiddenNodeIds.length} isolatedNodeId={isolatedNodeId} selectedCount={selectedNodeIds.length} />
            <AssemblyTree
              hiddenIds={hiddenNodeIds}
              isolatedNodeId={isolatedNodeId}
              nodes={filteredNodes}
              onHide={toggleHiddenNode}
              onIsolate={(nodeId) => useViewerStore.setState({ isolatedNodeId: isolatedNodeId === nodeId ? null : nodeId })}
              onReset={resetVisibility}
              onSelect={(nodeId) => setSelectedNodeIds([nodeId])}
              selectedIds={selectedNodeIds}
            />
          </div>
        </aside>
        <section className="bg-[var(--background-shell)] p-4">
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
        <aside className="border-l border-[var(--border-muted)] bg-[var(--background-surface)] px-4 py-4">
          <Card description="Real workflow truth from the backend orchestrator, DFM, and approval contracts." title="Intelligence">
            <Tabs
              items={[
                { id: "state", label: "State", content: <StatePanel decision={decision} /> },
                {
                  id: "inputs",
                  label: "Required Inputs",
                  content: <RequiredInputsPanel error={inputsError} fields={fields} onChange={setValue} onSubmit={handleSubmitInputs} values={values} />,
                },
                { id: "decision", label: "Decision", content: <DecisionPanel decision={decision} /> },
                { id: "risks", label: "Risks", content: <RisksPanel decision={decision} dfm={report} /> },
                { id: "dfm", label: "DFM Report", content: <DfmReportPanel report={report} rerunSupported={rerunSupported} /> },
                {
                  id: "activity",
                  label: "Activity",
                  content: <ActivityEvidencePanel createdAt={viewer.file.createdAt} shareCount={shares.length} status={viewer.file.status} />,
                },
                {
                  id: "approval",
                  label: "Approval",
                  content: <ApprovalPanel decision={decision} onApprove={(reason) => handleApproval("approve", reason)} onReject={(reason) => handleApproval("reject", reason)} />,
                },
              ]}
            />
          </Card>
        </aside>
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
