"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

import { Card } from "@/components/primitives/Card";
import { PageHeader } from "@/components/shell/PageHeader";
import { ShareDialog } from "@/components/shares/ShareDialog";
import { RouteErrorState } from "@/components/states/RouteErrorState";
import { RouteLoadingState } from "@/components/states/RouteLoadingState";
import { useProjectDetail } from "@/lib/hooks/useProjectDetail";
import { useShares } from "@/lib/hooks/useShares";
import { useUpload } from "@/lib/hooks/useUpload";

import { AttentionPanel } from "../dashboard/AttentionPanel";
import { UploadDropzone } from "../dashboard/UploadDropzone";
import { ProjectFilesTable } from "./ProjectFilesTable";

export interface ProjectDetailScreenProps {
  projectId: string;
}

export function ProjectDetailScreen({ projectId }: ProjectDetailScreenProps) {
  const router = useRouter();
  const { project, workflowSummary, loading, error, refresh } = useProjectDetail(projectId);
  const { items, upload } = useUpload();
  const { create } = useShares();
  const [shareDialogOpen, setShareDialogOpen] = React.useState(false);
  const [activeShareFileId, setActiveShareFileId] = React.useState<string | null>(null);

  if (loading) return <RouteLoadingState title="Loading project detail" />;
  if (error || !project) return <RouteErrorState actionLabel="Retry" description={error || "Project not found."} onAction={() => void refresh()} title="Project unavailable" />;

  return (
    <div className="space-y-6">
      <PageHeader
        subtitle="Inspect files, open operational routes, and upload additional files into the same project scope."
        title={project.name}
      />
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_340px]">
        <div className="space-y-6">
          <UploadDropzone
            onUpload={async (file) => {
              const fileId = await upload(file, project.projectId);
              if (fileId) router.push(`/files/${encodeURIComponent(fileId)}`);
            }}
            uploads={items}
          />
          <Card description="Project-bound files resolved from the live projects contract." title="Files">
            <ProjectFilesTable
              files={project.files}
              onShare={(selectedFileId) => {
                setActiveShareFileId(selectedFileId);
                setShareDialogOpen(true);
              }}
            />
          </Card>
        </div>
        <div className="space-y-6">
          <Card description="Project workflow counts derived from file status." title="Workflow summary">
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between">
                <dt className="text-[var(--foreground-soft)]">Ready</dt>
                <dd className="font-medium">{workflowSummary?.readyCount ?? 0}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-[var(--foreground-soft)]">Processing</dt>
                <dd className="font-medium">{workflowSummary?.processingCount ?? 0}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-[var(--foreground-soft)]">Failed</dt>
                <dd className="font-medium">{workflowSummary?.failedCount ?? 0}</dd>
              </div>
            </dl>
          </Card>
          <AttentionPanel
            files={project.files.map((file) => ({
              fileId: file.fileId,
              originalName: file.originalFilename,
              kind: file.kind || "unknown",
              mode: file.mode,
              createdAt: file.createdAt || new Date().toISOString(),
              contentType: "application/octet-stream",
              sizeBytes: 0,
              status: file.status,
              statusTone: "neutral",
              visibility: "private",
              thumbnailUrl: null,
              previewUrl: null,
              previewUrls: [],
              gltfUrl: null,
              originalUrl: null,
              partCount: null,
              error: null,
            }))}
          />
        </div>
      </div>
      <ShareDialog
        onClose={() => {
          setShareDialogOpen(false);
          setActiveShareFileId(null);
        }}
        onCreate={async (permission, expiresInSeconds) => {
          if (!activeShareFileId) throw new Error("Select a file before creating a share.");
          await create(activeShareFileId, permission, expiresInSeconds);
        }}
        open={shareDialogOpen}
      />
    </div>
  );
}
