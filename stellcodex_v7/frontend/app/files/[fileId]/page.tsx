"use client";

import { useParams } from "next/navigation";
import { AppShell } from "@/components/shell/AppShell";
import { ErrorState } from "@/components/primitives/ErrorState";
import { LoadingSkeleton } from "@/components/primitives/LoadingSkeleton";
import { FileHeader } from "@/components/files/FileHeader";
import { FileSharesPanel } from "@/components/files/FileSharesPanel";
import { FileStatusTimeline } from "@/components/files/FileStatusTimeline";
import { FileSummaryCard } from "@/components/files/FileSummaryCard";
import { FileVersionsTable } from "@/components/files/FileVersionsTable";
import { FileWorkflowPanel } from "@/components/files/FileWorkflowPanel";
import { useFileDetail } from "@/lib/hooks/useFileDetail";
import { useOrchestratorSession } from "@/lib/hooks/useOrchestratorSession";
import { useShares } from "@/lib/hooks/useShares";

export default function FileDetailPage() {
  const params = useParams<{ fileId: string }>();
  const fileId = params.fileId;
  const { file, versions, timeline, loading, error, refresh } = useFileDetail(fileId);
  const { state } = useOrchestratorSession(fileId);
  const { data: shares, revoke } = useShares(fileId);

  return (
    <AppShell
      title="File detail"
      subtitle="Versions, workflow, and shares"
      breadcrumbs={[
        { href: "/files", label: "Files" },
        { label: file?.fileName || fileId },
      ]}
    >
      {loading ? <LoadingSkeleton label="Loading file detail" /> : null}
      {error ? <ErrorState title="File unavailable" description={error} retryLabel="Retry" onRetry={() => void refresh()} /> : null}
      {file ? (
        <div className="sc-stack">
          <FileHeader file={file} />
          <div className="sc-grid sc-grid-3">
            <FileSummaryCard file={file} />
            <FileWorkflowPanel workflow={state} />
            <FileSharesPanel shares={shares} onRevoke={(shareId) => void revoke(shareId)} />
          </div>
          <FileStatusTimeline events={timeline} />
          <FileVersionsTable versions={versions} />
        </div>
      ) : null}
    </AppShell>
  );
}
