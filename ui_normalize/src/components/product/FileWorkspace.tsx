"use client";

import * as React from "react";
import Link from "next/link";

import { FileStatusBadge } from "@/components/files/FileStatusBadge";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { EmptyState } from "@/components/primitives/EmptyState";
import { ShareDialog } from "@/components/shares/ShareDialog";
import { ShareTable } from "@/components/shares/ShareTable";
import { RouteErrorState } from "@/components/states/RouteErrorState";
import { RouteLoadingState } from "@/components/states/RouteLoadingState";
import { useFileDetail } from "@/lib/hooks/useFileDetail";
import { useDfmReport } from "@/lib/hooks/useDfmReport";
import { useShares } from "@/lib/hooks/useShares";
import { formatBytes, formatDateTime } from "@/lib/utils";

export interface FileWorkspaceProps {
  fileId: string;
}

export function FileWorkspace({ fileId }: FileWorkspaceProps) {
  const { file, decision, projectName, shares: fileShares, loading, error, refresh } = useFileDetail(fileId);
  const { report } = useDfmReport(fileId);
  const { create, revoke, copyLink, openLink, shares } = useShares(fileId);
  const [shareDialogOpen, setShareDialogOpen] = React.useState(false);

  const activeShares = shares.length > 0 ? shares : fileShares;

  if (loading) return <RouteLoadingState title="Loading file workspace" />;
  if (error || !file) return <RouteErrorState actionLabel="Retry" description={error || "File not found."} onAction={() => void refresh()} title="File unavailable" />;

  const findings = report?.findings ?? [];

  return (
    <div className="mx-auto max-w-[900px] space-y-6">
      <Card
        actions={
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => setShareDialogOpen(true)} size="sm" variant="secondary">
              Create Share
            </Button>
            <Link href={`/files/${encodeURIComponent(file.fileId)}/viewer`}>
              <Button size="sm" variant="primary">
                Open Viewer
              </Button>
            </Link>
          </div>
        }
        title={file.originalName}
      >
        <div className="space-y-2 text-sm text-[var(--foreground-muted)]">
          <div>{file.fileId}</div>
          <div>{projectName || "Not linked"}</div>
        </div>
      </Card>

      <Card title="Details">
        <div className="space-y-3 text-sm">
          <div className="flex items-center justify-between gap-4">
            <span className="text-[var(--foreground-muted)]">Status</span>
            <FileStatusBadge status={file.status} />
          </div>
          <div className="flex items-center justify-between gap-4">
            <span className="text-[var(--foreground-muted)]">Kind</span>
            <span className="text-[var(--foreground-strong)]">{file.kind}</span>
          </div>
          <div className="flex items-center justify-between gap-4">
            <span className="text-[var(--foreground-muted)]">Mode</span>
            <span className="text-[var(--foreground-strong)]">{file.mode || "Unknown"}</span>
          </div>
          <div className="flex items-center justify-between gap-4">
            <span className="text-[var(--foreground-muted)]">Size</span>
            <span className="text-[var(--foreground-strong)]">{formatBytes(file.sizeBytes)}</span>
          </div>
          <div className="flex items-center justify-between gap-4">
            <span className="text-[var(--foreground-muted)]">Created</span>
            <span className="text-right text-[var(--foreground-strong)]">{formatDateTime(file.createdAt)}</span>
          </div>
          <div className="flex items-center justify-between gap-4">
            <span className="text-[var(--foreground-muted)]">Project</span>
            <span className="text-right text-[var(--foreground-strong)]">{projectName || "Not linked"}</span>
          </div>
        </div>
      </Card>

      <Card title="Workflow">
        <div className="space-y-3 text-sm">
          <div className="flex items-center justify-between gap-4">
            <span className="text-[var(--foreground-muted)]">DFM gate</span>
            <span className="text-[var(--foreground-strong)]">{report?.statusGate || "Unavailable"}</span>
          </div>
          <div className="flex items-center justify-between gap-4">
            <span className="text-[var(--foreground-muted)]">Decision state</span>
            <span className="text-[var(--foreground-strong)]">{decision?.stateLabel || "Unavailable"}</span>
          </div>
          <div className="flex items-center justify-between gap-4">
            <span className="text-[var(--foreground-muted)]">Shares</span>
            <span className="text-[var(--foreground-strong)]">{activeShares.length}</span>
          </div>
        </div>
      </Card>

      <Card title="Decision">
        {!decision ? (
          <EmptyState description="No decision payload is available." title="Decision unavailable" />
        ) : (
          <div className="space-y-3 text-sm">
            <div className="flex items-center justify-between gap-4">
              <span className="text-[var(--foreground-muted)]">Method</span>
              <span className="text-[var(--foreground-strong)]">{decision.manufacturingMethod}</span>
            </div>
            <div className="flex items-center justify-between gap-4">
              <span className="text-[var(--foreground-muted)]">Mode</span>
              <span className="text-[var(--foreground-strong)]">{decision.mode}</span>
            </div>
            <div className="flex items-center justify-between gap-4">
              <span className="text-[var(--foreground-muted)]">Confidence</span>
              <span className="text-[var(--foreground-strong)]">{decision.confidence.toFixed(3)}</span>
            </div>
          </div>
        )}
      </Card>

      <Card title="Risks">
        {findings.length === 0 && (!decision || decision.riskFlags.length === 0) ? (
          <EmptyState description="No risks are attached to this file." title="No risks" />
        ) : (
          <div className="space-y-3">
            {decision?.riskFlags.map((flag) => (
              <div className="rounded-[12px] border border-[#eeeeee] p-4" key={flag}>
                <div className="text-sm font-semibold text-[var(--foreground-strong)]">{flag}</div>
              </div>
            ))}
            {findings.slice(0, 4).map((finding) => (
              <div className="rounded-[12px] border border-[#eeeeee] p-4" key={`${finding.code}-${finding.message}`}>
                <div className="text-sm font-semibold text-[var(--foreground-strong)]">{finding.code}</div>
                <div className="mt-1 text-sm text-[var(--foreground-muted)]">{finding.severity}</div>
                <div className="mt-2 text-sm text-[var(--foreground-default)]">{finding.message}</div>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card title="Shares">
        <ShareTable onCopy={copyLink} onOpen={openLink} onRevoke={revoke} shares={activeShares} />
      </Card>

      <Card title="Open">
        <div className="flex flex-wrap gap-2">
          <Link href={`/files/${encodeURIComponent(file.fileId)}/viewer`}>
            <Button size="sm" variant="secondary">
              Viewer
            </Button>
          </Link>
          <Link href="/projects">
            <Button size="sm" variant="secondary">
              Projects
            </Button>
          </Link>
        </div>
      </Card>

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
