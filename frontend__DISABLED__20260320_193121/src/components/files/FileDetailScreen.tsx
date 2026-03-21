"use client";

import * as React from "react";
import Link from "next/link";

import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { PageHeader } from "@/components/shell/PageHeader";
import { RouteErrorState } from "@/components/states/RouteErrorState";
import { RouteLoadingState } from "@/components/states/RouteLoadingState";
import { useFileDetail } from "@/lib/hooks/useFileDetail";
import { useDfmReport } from "@/lib/hooks/useDfmReport";
import { useShares } from "@/lib/hooks/useShares";

import { ShareDialog } from "../shares/ShareDialog";
import { ShareTable } from "../shares/ShareTable";
import { FileMetaCard } from "./FileMetaCard";
import { VersionsTable } from "./VersionsTable";
import { WorkflowSummaryCard } from "./WorkflowSummaryCard";

export interface FileDetailScreenProps {
  fileId: string;
}

export function FileDetailScreen({ fileId }: FileDetailScreenProps) {
  const { file, decision, projectName, shares: fileShares, versionsSupported, loading, error, refresh } = useFileDetail(fileId);
  const { report } = useDfmReport(fileId);
  const { create, revoke, copyLink, openLink, shares } = useShares(fileId);
  const [shareDialogOpen, setShareDialogOpen] = React.useState(false);

  const activeShares = shares.length > 0 ? shares : fileShares;

  if (loading) return <RouteLoadingState title="Loading file detail" />;
  if (error || !file) return <RouteErrorState actionLabel="Retry" description={error || "File not found."} onAction={() => void refresh()} title="File unavailable" />;

  return (
    <div className="space-y-6">
      <PageHeader
        actions={
          <div className="flex gap-3">
            <Button onClick={() => setShareDialogOpen(true)} variant="secondary">
              Create share
            </Button>
            <Link href={`/files/${encodeURIComponent(file.fileId)}/viewer`}>
              <Button variant="primary">Open viewer</Button>
            </Link>
          </div>
        }
        subtitle="Operate a file from one hub: status, workflow, versions, shares, and viewer entry."
        title={file.originalName}
      />
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_minmax(320px,420px)]">
        <div className="space-y-6">
          <FileMetaCard file={file} projectName={projectName} />
          <WorkflowSummaryCard decision={decision} dfm={report} shareCount={activeShares.length} status={file.status} />
          <Card description="Live share list and revoke/copy/open controls for the current file." title="Shares">
            <ShareTable onCopy={copyLink} onOpen={openLink} onRevoke={revoke} shares={activeShares} />
          </Card>
        </div>
        <div className="space-y-6">
          <VersionsTable supported={versionsSupported} />
          <Card description="Open the workstation, public share flow, or version surface from the file hub." title="Actions">
            <div className="grid gap-3">
              <Link href={`/files/${encodeURIComponent(file.fileId)}/viewer`}>
                <Button className="w-full justify-between" variant="secondary">
                  Viewer
                  <span>Open</span>
                </Button>
              </Link>
              <Link href={`/files/${encodeURIComponent(file.fileId)}/versions`}>
                <Button className="w-full justify-between" variant="secondary">
                  Versions
                  <span>Open</span>
                </Button>
              </Link>
            </div>
          </Card>
        </div>
      </div>
      <ShareDialog
        onClose={() => setShareDialogOpen(false)}
        onCreate={async (permission, expiresInSeconds) => {
          await create(file.fileId, permission, expiresInSeconds);
        }}
        open={shareDialogOpen}
      />
    </div>
  );
}
