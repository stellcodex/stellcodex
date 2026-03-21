"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { EmptyState } from "@/components/primitives/EmptyState";
import { Input } from "@/components/primitives/Input";
import { Select } from "@/components/primitives/Select";
import { FileStatusBadge } from "@/components/files/FileStatusBadge";
import { RouteErrorState } from "@/components/states/RouteErrorState";
import { RouteLoadingState } from "@/components/states/RouteLoadingState";
import { listRecentFiles } from "@/lib/api/files";
import { createProject } from "@/lib/api/projects";
import type { FileRecord, ProjectRecord } from "@/lib/contracts/ui";
import { useProjects } from "@/lib/hooks/useProjects";
import { useUpload } from "@/lib/hooks/useUpload";
import { mapFileRecord } from "@/lib/mappers/fileMappers";
import { formatBytes, formatDate, formatDateTime } from "@/lib/utils";

function countProjectReady(project: ProjectRecord) {
  return project.files.filter((file) => file.status.toLowerCase() === "ready").length;
}

function countProjectActive(project: ProjectRecord) {
  return project.files.filter((file) => ["queued", "processing", "running"].includes(file.status.toLowerCase())).length;
}

function countProjectFailed(project: ProjectRecord) {
  return project.files.filter((file) => file.status.toLowerCase() === "failed").length;
}

export function DashboardWorkspace() {
  const router = useRouter();
  const inputRef = React.useRef<HTMLInputElement | null>(null);
  const { projects, loading: projectsLoading, error: projectsError, refresh: refreshProjects } = useProjects();
  const { items, upload, error: uploadError } = useUpload();
  const [files, setFiles] = React.useState<FileRecord[]>([]);
  const [filesLoading, setFilesLoading] = React.useState(true);
  const [filesError, setFilesError] = React.useState<string | null>(null);
  const [selectedProjectId, setSelectedProjectId] = React.useState("");
  const [draftProjectName, setDraftProjectName] = React.useState("");
  const [intakeError, setIntakeError] = React.useState<string | null>(null);
  const [creatingProject, setCreatingProject] = React.useState(false);

  const refreshFiles = React.useCallback(async () => {
    setFilesLoading(true);
    setFilesError(null);
    try {
      const rows = await listRecentFiles(12);
      setFiles(rows.map(mapFileRecord));
    } catch (caughtError) {
      setFilesError(caughtError instanceof Error ? caughtError.message : "Recent files could not be loaded.");
    } finally {
      setFilesLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void refreshFiles();
  }, [refreshFiles]);

  async function createProjectWorkspace() {
    if (!draftProjectName.trim()) {
      setIntakeError("Enter a project name before creating a workspace.");
      return null;
    }

    setCreatingProject(true);
    setIntakeError(null);
    try {
      const project = await createProject(draftProjectName.trim());
      setDraftProjectName("");
      setSelectedProjectId(project.id);
      await refreshProjects();
      return project.id;
    } catch (caughtError) {
      const message = caughtError instanceof Error ? caughtError.message : "Project creation failed.";
      setIntakeError(message);
      return null;
    } finally {
      setCreatingProject(false);
    }
  }

  async function resolveProjectId() {
    if (selectedProjectId) return selectedProjectId;
    return createProjectWorkspace();
  }

  async function handleUpload(fileList: FileList | null) {
    const file = fileList?.[0];
    if (!file) return;

    try {
      setIntakeError(null);
      const projectId = await resolveProjectId();
      if (!projectId) return;
      await upload(file, projectId);
      await Promise.all([refreshProjects(), refreshFiles()]);
      router.push(`/projects/${encodeURIComponent(projectId)}`);
    } catch (caughtError) {
      setIntakeError(caughtError instanceof Error ? caughtError.message : "Upload failed.");
    }
  }

  if (projectsLoading && filesLoading) {
    return <RouteLoadingState title="Loading dashboard workspace" />;
  }

  if (projectsError || filesError) {
    return (
      <RouteErrorState
        actionLabel="Retry"
        description={projectsError || filesError || "Dashboard data could not be loaded."}
        onAction={() => {
          void refreshProjects();
          void refreshFiles();
        }}
        title="Dashboard unavailable"
      />
    );
  }

  const attentionFiles = files.filter((file) => ["failed", "queued", "processing", "running"].includes(file.status.toLowerCase()));

  return (
    <div className="mx-auto max-w-[900px] space-y-6">
      <Card title="Upload">
        <div className="space-y-4" id="intake">
          <div className="space-y-2">
            <div className="text-sm text-[var(--foreground-default)]">Project</div>
            <Select onChange={(event) => setSelectedProjectId(event.target.value)} value={selectedProjectId}>
              <option value="">Create from new project name</option>
              {projects.map((project) => (
                <option key={project.projectId} value={project.projectId}>
                  {project.name}
                </option>
              ))}
            </Select>
          </div>

          <div className="space-y-2">
            <div className="text-sm text-[var(--foreground-default)]">New project name</div>
            <Input onChange={(event) => setDraftProjectName(event.target.value)} placeholder="Project name" value={draftProjectName} />
          </div>

          <div
            className="rounded-[12px] border border-[#eee] px-4 py-6"
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
            <div className="mt-4 flex items-center gap-3">
              <Button className="shrink-0" size="sm" variant="primary">
                Select File
              </Button>
              <Button
                onClick={(event) => {
                  event.stopPropagation();
                  void createProjectWorkspace();
                }}
                size="sm"
                variant="secondary"
              >
                {creatingProject ? "Creating..." : "Create Project"}
              </Button>
            </div>
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
                <div key={item.localId} className="rounded-[12px] border border-[#eee] p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <div className="truncate text-sm text-[var(--foreground-strong)]">{item.fileName}</div>
                      <div className="text-sm text-[var(--foreground-muted)]">
                        {item.fileId ? `file_id ${item.fileId}` : item.error || item.status}
                      </div>
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

      <Card title="Projects">
        {projects.length === 0 ? (
          <EmptyState description="Create a project to start routing work." title="No projects" />
        ) : (
          <div className="space-y-3">
            {projects.slice(0, 10).map((project) => (
              <Link
                className="block rounded-[12px] border border-[#eee] p-4 transition-colors hover:bg-[var(--background-muted)]"
                href={`/projects/${encodeURIComponent(project.projectId)}`}
                key={project.projectId}
              >
                <div className="text-sm font-semibold text-[var(--foreground-strong)]">{project.name}</div>
                <div className="mt-1 text-sm text-[var(--foreground-muted)]">
                  {project.fileCount} files · {countProjectReady(project)} ready · {countProjectActive(project)} active · {countProjectFailed(project)} failed
                </div>
                <div className="mt-1 text-sm text-[var(--foreground-muted)]">{formatDate(project.updatedAt)}</div>
              </Link>
            ))}
          </div>
        )}
      </Card>

      <Card title="Recent Files">
        {files.length === 0 ? (
          <EmptyState description="Recent files appear after upload." title="No recent files" />
        ) : (
          <div className="space-y-3">
            {files.map((file) => (
              <Link
                className="flex items-start justify-between gap-3 rounded-[12px] border border-[#eee] p-4 transition-colors hover:bg-[var(--background-muted)]"
                href={`/files/${encodeURIComponent(file.fileId)}`}
                key={file.fileId}
              >
                <div className="min-w-0">
                  <div className="truncate text-sm font-semibold text-[var(--foreground-strong)]">{file.originalName}</div>
                  <div className="mt-1 text-sm text-[var(--foreground-muted)]">{file.fileId}</div>
                  <div className="mt-1 text-sm text-[var(--foreground-muted)]">
                    {formatBytes(file.sizeBytes)} · {formatDateTime(file.createdAt)}
                  </div>
                </div>
                <FileStatusBadge status={file.status} />
              </Link>
            ))}
          </div>
        )}
      </Card>

      <Card title="Attention">
        {attentionFiles.length === 0 ? (
          <EmptyState description="There is nothing waiting for review." title="Queue clear" />
        ) : (
          <div className="space-y-3">
            {attentionFiles.slice(0, 6).map((file) => (
              <Link
                className="flex items-start justify-between gap-3 rounded-[12px] border border-[#eee] p-4 transition-colors hover:bg-[var(--background-muted)]"
                href={`/files/${encodeURIComponent(file.fileId)}`}
                key={file.fileId}
              >
                <div className="min-w-0">
                  <div className="truncate text-sm font-semibold text-[var(--foreground-strong)]">{file.originalName}</div>
                  <div className="mt-1 text-sm text-[var(--foreground-muted)]">{file.fileId}</div>
                </div>
                <FileStatusBadge status={file.status} />
              </Link>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}
