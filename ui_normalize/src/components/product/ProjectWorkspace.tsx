"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { FileStatusBadge } from "@/components/files/FileStatusBadge";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { EmptyState } from "@/components/primitives/EmptyState";
import { ShareDialog } from "@/components/shares/ShareDialog";
import { RouteErrorState } from "@/components/states/RouteErrorState";
import { RouteLoadingState } from "@/components/states/RouteLoadingState";
import { useProjectDetail } from "@/lib/hooks/useProjectDetail";
import { useShares } from "@/lib/hooks/useShares";
import { useUpload } from "@/lib/hooks/useUpload";
import { formatDateTime } from "@/lib/utils";

export interface ProjectWorkspaceProps {
  projectId: string;
}

export function ProjectWorkspace({ projectId }: ProjectWorkspaceProps) {
  const router = useRouter();
  const inputRef = React.useRef<HTMLInputElement | null>(null);
  const { project, workflowSummary, loading, error, refresh } = useProjectDetail(projectId);
  const { items, upload, error: uploadError } = useUpload();
  const { create } = useShares();
  const [shareDialogOpen, setShareDialogOpen] = React.useState(false);
  const [activeShareFileId, setActiveShareFileId] = React.useState<string | null>(null);
  const [intakeError, setIntakeError] = React.useState<string | null>(null);

  async function handleUpload(fileList: FileList | null) {
    const file = fileList?.[0];
    if (!file || !project) return;
    try {
      setIntakeError(null);
      const fileId = await upload(file, project.projectId);
      await refresh();
      router.push(`/files/${encodeURIComponent(fileId)}`);
    } catch (caughtError) {
      setIntakeError(caughtError instanceof Error ? caughtError.message : "Upload failed.");
    }
  }

  if (loading) return <RouteLoadingState title="Loading project workspace" />;
  if (error || !project) return <RouteErrorState actionLabel="Retry" description={error || "Project not found."} onAction={() => void refresh()} title="Project unavailable" />;

  const attentionFiles = project.files.filter((file) => ["queued", "processing", "running", "failed"].includes(file.status.toLowerCase()));

  return (
    <div className="mx-auto max-w-[900px] space-y-6">
      <Card
        actions={
          <Link href="/projects">
            <Button size="sm" variant="secondary">
              Back to Projects
            </Button>
          </Link>
        }
        title={project.name}
      >
        <div className="space-y-2 text-sm text-[var(--foreground-muted)]">
          <div>{project.projectId}</div>
          <div>
            {project.fileCount} files · {workflowSummary?.readyCount ?? 0} ready · {workflowSummary?.processingCount ?? 0} active · {workflowSummary?.failedCount ?? 0} failed
          </div>
        </div>
      </Card>

      <Card title="Upload">
        <div className="space-y-4">
          <div
            className="rounded-[12px] border border-[#eeeeee] px-4 py-6"
            onClick={() => inputRef.current?.click()}
            onDragOver={(event) => event.preventDefault()}
            onDrop={(event) => {
              event.preventDefault();
              void handleUpload(event.dataTransfer.files);
            }}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                inputRef.current?.click();
              }
            }}
            role="button"
            tabIndex={0}
          >
            <div className="text-sm text-[var(--foreground-default)]">Drop a file here or select one.</div>
            <Button className="mt-4" size="sm" variant="primary">
              Select File
            </Button>
            <input
              className="hidden"
              onChange={(event) => {
                void handleUpload(event.target.files);
                event.currentTarget.value = "";
              }}
              ref={inputRef}
              type="file"
            />
          </div>

          {intakeError || uploadError ? <div className="text-sm text-[var(--foreground-default)]">{intakeError || uploadError}</div> : null}

          {items.length > 0 ? (
            <div className="space-y-3">
              {items.map((item) => (
                <div key={item.localId} className="rounded-[12px] border border-[#eeeeee] p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <div className="truncate text-sm font-medium text-[var(--foreground-strong)]">{item.fileName}</div>
                      <div className="text-sm text-[var(--foreground-muted)]">{item.fileId ? `file_id ${item.fileId}` : item.error || item.status}</div>
                    </div>
                    <div className="text-sm text-[var(--foreground-muted)]">{item.progress}%</div>
                  </div>
                  <div className="mt-3 h-2 rounded-full bg-[var(--background-subtle)]">
                    <div className="h-full rounded-full bg-[var(--accent-default)]" style={{ width: `${item.progress}%` }} />
                  </div>
                </div>
              ))}
            </div>
          ) : null}
        </div>
      </Card>

      <Card title="Files">
        {project.files.length === 0 ? (
          <EmptyState description="Upload a file to start." title="No files" />
        ) : (
          <div className="space-y-3">
            {project.files.map((file) => (
              <div key={file.fileId} className="rounded-[12px] border border-[#eeeeee] p-4">
                <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
                  <div className="min-w-0 space-y-1">
                    <div className="truncate text-sm font-semibold text-[var(--foreground-strong)]">{file.originalFilename}</div>
                    <div className="text-sm text-[var(--foreground-muted)]">{file.fileId}</div>
                    <div className="text-sm text-[var(--foreground-muted)]">
                      {file.mode || "Unknown"} · {formatDateTime(file.createdAt)}
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-3">
                    <FileStatusBadge status={file.status} />
                    <Link className="text-sm text-[var(--foreground-default)]" href={`/files/${encodeURIComponent(file.fileId)}`}>
                      File
                    </Link>
                    <Link className="text-sm text-[var(--foreground-default)]" href={`/files/${encodeURIComponent(file.fileId)}/viewer`}>
                      Viewer
                    </Link>
                    <button
                      className="text-sm text-[var(--foreground-default)]"
                      onClick={() => {
                        setActiveShareFileId(file.fileId);
                        setShareDialogOpen(true);
                      }}
                      type="button"
                    >
                      Share
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card title="Attention">
        {attentionFiles.length === 0 ? (
          <EmptyState description="There is nothing waiting here." title="Queue clear" />
        ) : (
          <div className="space-y-3">
            {attentionFiles.map((file) => (
              <Link
                className="flex items-center justify-between gap-3 rounded-[12px] border border-[#eeeeee] p-4 transition-colors hover:bg-[var(--background-muted)]"
                href={`/files/${encodeURIComponent(file.fileId)}`}
                key={file.fileId}
              >
                <div className="min-w-0">
                  <div className="truncate text-sm font-semibold text-[var(--foreground-strong)]">{file.originalFilename}</div>
                  <div className="text-sm text-[var(--foreground-muted)]">{file.fileId}</div>
                </div>
                <FileStatusBadge status={file.status} />
              </Link>
            ))}
          </div>
        )}
      </Card>

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
