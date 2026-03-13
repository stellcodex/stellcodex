"use client";

import { useParams } from "next/navigation";
import { useMemo, useState } from "react";
import { approve, reject } from "@/lib/api/approvals";
import { AppShell } from "@/components/shell/AppShell";
import { ErrorState } from "@/components/primitives/ErrorState";
import { ViewerLayout } from "@/components/viewer/ViewerLayout";
import { ViewerToolbar } from "@/components/viewer/ViewerToolbar";
import { ViewerCanvas } from "@/components/viewer/ViewerCanvas";
import { ViewerLoadingState } from "@/components/viewer/ViewerLoadingState";
import { ViewerProcessingState } from "@/components/viewer/ViewerProcessingState";
import { SelectionInspector } from "@/components/viewer/SelectionInspector";
import { AssemblyTree } from "@/components/viewer/AssemblyTree";
import { IntelligencePanel } from "@/components/intelligence/IntelligencePanel";
import { useViewerData } from "@/lib/hooks/useViewerData";
import { useDfmReport } from "@/lib/hooks/useDfmReport";
import { useRequiredInputs } from "@/lib/hooks/useRequiredInputs";
import type { ViewerOccurrenceNode } from "@/lib/contracts/viewer";

export default function FileViewerPage() {
  const params = useParams<{ fileId: string }>();
  const fileId = params.fileId;
  const { file, viewer, state, decision, risks, activity, loading, error, refresh } = useViewerData(fileId);
  const { report, rerun, running } = useDfmReport(fileId);
  const { fields, updateField } = useRequiredInputs([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [approvalBusy, setApprovalBusy] = useState(false);
  const [fitRequestKey, setFitRequestKey] = useState(0);

  const selectedNode = useMemo(() => {
    const walk = (nodes: ViewerOccurrenceNode[]): ViewerOccurrenceNode | null => {
      for (const node of nodes) {
        if (node.nodeId === selectedNodeId) return node;
        const child = walk(node.children || []);
        if (child) return child;
      }
      return null;
    };
    return viewer ? walk(viewer.assemblyTree) : null;
  }, [selectedNodeId, viewer]);

  const filteredTree = useMemo(() => {
    if (!viewer) return [];
    if (!searchQuery.trim()) return viewer.assemblyTree;
    const token = searchQuery.toLowerCase();
    const filterNodes = (nodes: typeof viewer.assemblyTree): typeof viewer.assemblyTree =>
      nodes
        .map((node) => ({
          ...node,
          selected: node.nodeId === selectedNodeId,
          children: filterNodes(node.children || []),
        }))
        .filter((node) => node.label.toLowerCase().includes(token) || (node.children || []).length > 0);
    return filterNodes(viewer.assemblyTree);
  }, [viewer, searchQuery, selectedNodeId]);

  async function handleApprove() {
    if (!state?.sessionId) return;
    setApprovalBusy(true);
    try {
      await approve(state.sessionId);
      await refresh();
    } finally {
      setApprovalBusy(false);
    }
  }

  async function handleReject() {
    if (!state?.sessionId) return;
    setApprovalBusy(true);
    try {
      await reject(state.sessionId);
      await refresh();
    } finally {
      setApprovalBusy(false);
    }
  }

  return (
    <AppShell
      title="Viewer"
      subtitle="Occurrence-driven engineering viewer"
      breadcrumbs={[
        { href: "/files", label: "Files" },
        { href: `/files/${fileId}`, label: file?.fileName || fileId },
        { label: "Viewer" },
      ]}
    >
      {loading ? <ViewerLoadingState /> : null}
      {error ? <ErrorState title="Viewer unavailable" description={error} retryLabel="Retry" onRetry={() => void refresh()} /> : null}
      {!loading && file && viewer ? (
        <ViewerLayout
          toolbar={
            <ViewerToolbar
              file={file}
              onFit={() => setFitRequestKey((value) => value + 1)}
              onReset={() => {
                setSelectedNodeId(null);
                setSearchQuery("");
                setFitRequestKey((value) => value + 1);
              }}
              shareHref={`/shares?fileId=${file.fileId}`}
            />
          }
          left={
            <AssemblyTree
              nodes={filteredTree}
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
              onSelect={(node) => setSelectedNodeId(node.nodeId)}
              onShowAll={() => undefined}
              onHideSelected={() => undefined}
              disableShowAll
              disableHide
              visibilityHint="Visibility controls unavailable: render-node bindings are not exposed by the active viewer."
            />
          }
          center={
            viewer.status === "processing" ? (
              <ViewerProcessingState />
            ) : (
              <ViewerCanvas fileId={fileId} viewer={viewer} fitRequestKey={fitRequestKey} />
            )
          }
          right={
            <div className="sc-stack">
              <SelectionInspector selectedNode={selectedNode} />
              <IntelligencePanel
                state={state}
                decision={decision}
                fields={fields}
                risks={risks}
                report={report}
                activity={activity}
                onRefresh={() => void refresh()}
                onAdvance={() => void refresh()}
                onFieldChange={updateField}
                onSubmitInputs={() => void refresh()}
                onApprove={state?.approvalRequired ? handleApprove : undefined}
                onReject={state?.approvalRequired ? handleReject : undefined}
                onRerunDfm={() => void rerun()}
                approvalBusy={approvalBusy}
                dfmBusy={running}
              />
            </div>
          }
        />
      ) : null}
    </AppShell>
  );
}
