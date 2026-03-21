"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

import { AdminFailedJobsTable } from "@/components/admin/AdminFailedJobsTable";
import { AdminQueuesTable } from "@/components/admin/AdminQueuesTable";
import { Card } from "@/components/primitives/Card";
import { EmptyState } from "@/components/primitives/EmptyState";
import { PageHeader } from "@/components/shell/PageHeader";
import { RouteErrorState } from "@/components/states/RouteErrorState";
import { RouteLoadingState } from "@/components/states/RouteLoadingState";
import { getAdminFailedJobs, getAdminQueues } from "@/lib/api/admin";
import { listFiles } from "@/lib/api/files";
import { useProjects } from "@/lib/hooks/useProjects";
import { useUpload } from "@/lib/hooks/useUpload";
import { mapAdminFailedJob, mapAdminQueue } from "@/lib/mappers/adminMappers";
import { mapFileRecord } from "@/lib/mappers/fileMappers";

import { RecentFilesTable } from "./RecentFilesTable";
import { RecentProjectsTable } from "./RecentProjectsTable";
import { UploadDropzone } from "./UploadDropzone";

export function DashboardScreen() {
  const router = useRouter();
  const { projects, loading: projectsLoading, error: projectsError, refresh: refreshProjects } = useProjects();
  const { items, upload, error: uploadError } = useUpload();
  const [files, setFiles] = React.useState<ReturnType<typeof mapFileRecord>[]>([]);
  const [filesLoading, setFilesLoading] = React.useState(true);
  const [filesError, setFilesError] = React.useState<string | null>(null);
  const [queues, setQueues] = React.useState<ReturnType<typeof mapAdminQueue>[]>([]);
  const [failedJobs, setFailedJobs] = React.useState<ReturnType<typeof mapAdminFailedJob>[]>([]);
  const [opsLoading, setOpsLoading] = React.useState(true);
  const [opsError, setOpsError] = React.useState<string | null>(null);

  const refreshFiles = React.useCallback(async () => {
    setFilesLoading(true);
    setFilesError(null);
    try {
      const rows = await listFiles();
      setFiles(rows.map(mapFileRecord).slice(0, 8));
    } catch (caughtError) {
      setFilesError(caughtError instanceof Error ? caughtError.message : "Recent files could not be loaded.");
    } finally {
      setFilesLoading(false);
    }
  }, []);

  const refreshOps = React.useCallback(async () => {
    setOpsLoading(true);
    setOpsError(null);
    try {
      const [queueRows, failedRows] = await Promise.all([getAdminQueues(), getAdminFailedJobs()]);
      setQueues(queueRows.map(mapAdminQueue));
      setFailedJobs(failedRows.map(mapAdminFailedJob));
    } catch (caughtError) {
      setQueues([]);
      setFailedJobs([]);
      setOpsError(caughtError instanceof Error ? caughtError.message : "Recent job data could not be loaded.");
    } finally {
      setOpsLoading(false);
    }
  }, []);

  React.useEffect(() => {
    void refreshFiles();
  }, [refreshFiles]);

  React.useEffect(() => {
    void refreshOps();
  }, [refreshOps]);

  if (projectsLoading && filesLoading && opsLoading) {
    return <RouteLoadingState title="Loading dashboard" />;
  }

  if (projectsError || filesError) {
    return (
      <RouteErrorState
        actionLabel="Retry"
        description={projectsError || filesError || uploadError || "Dashboard data could not be loaded."}
        onAction={() => {
          void refreshProjects();
          void refreshFiles();
          void refreshOps();
        }}
        title="Dashboard unavailable"
      />
    );
  }

  const projectFileRows = projects.flatMap((project) => project.files);
  const readyFiles = projectFileRows.filter((file) => file.status.toLowerCase() === "ready").length;
  const activeFiles = projectFileRows.filter((file) => ["queued", "processing", "running"].includes(file.status.toLowerCase())).length;
  const failedFiles = projectFileRows.filter((file) => file.status.toLowerCase() === "failed").length;
  const queuedJobs = queues.reduce((total, item) => total + item.queuedCount, 0);
  const startedJobs = queues.reduce((total, item) => total + item.startedCount, 0);
  const failedJobCount = queues.reduce((total, item) => total + item.failedCount, 0);

  const summaryItems = [
    { label: "Projects", value: String(projects.length) },
    { label: "Files", value: String(files.length) },
    { label: "Ready", value: String(readyFiles) },
    { label: "Processing", value: String(activeFiles) },
    { label: "Failed", value: String(failedFiles) },
    { label: "Queued jobs", value: opsError ? "Unavailable" : String(queuedJobs) },
    { label: "Started jobs", value: opsError ? "Unavailable" : String(startedJobs) },
    { label: "Failed jobs", value: opsError ? "Unavailable" : String(failedJobCount) },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        subtitle="Upload files, inspect recent work, and review live queue state without leaving the manufacturing flow."
        title="Dashboard"
      />
      <UploadDropzone
        onUpload={async (file) => {
          const fileId = await upload(file);
          if (fileId) router.push(`/files/${encodeURIComponent(fileId)}`);
        }}
        uploads={items}
      />
      {uploadError ? (
        <Card title="Upload error">
          <div className="text-sm text-[var(--foreground-muted)]">{uploadError}</div>
        </Card>
      ) : null}
      <Card description="Workspace totals are computed from live project, file, and safe queue APIs." title="System summary">
        <dl className="grid gap-4 text-sm md:grid-cols-4">
          {summaryItems.map((item) => (
            <div key={item.label} className="rounded-[12px] border border-[#eeeeee] px-4 py-3">
              <dt className="text-[var(--foreground-soft)]">{item.label}</dt>
              <dd className="mt-2 font-medium text-[var(--foreground-strong)]">{item.value}</dd>
            </div>
          ))}
        </dl>
        {opsError ? (
          <div className="mt-4 rounded-[12px] border border-[#eeeeee] px-4 py-3 text-sm text-[var(--foreground-muted)]">
            Queue and recent job details are not available for this session: {opsError}
          </div>
        ) : null}
      </Card>
      <Card description="Recent project workspaces resolved from the live project contract." title="Recent projects">
        <RecentProjectsTable projects={projects.slice(0, 6)} />
      </Card>
      <Card description="Latest files and worker outputs returned by the files API." title="Recent files">
        <RecentFilesTable files={files} />
      </Card>
      <Card description="The current safe jobs surface comes from admin queue failures only." title="Recent jobs">
        {opsLoading ? (
          <EmptyState description="Recent job data is loading." title="Loading jobs" />
        ) : opsError ? (
          <EmptyState description={opsError} title="Recent jobs unavailable" />
        ) : (
          <AdminFailedJobsTable items={failedJobs.slice(0, 8)} />
        )}
      </Card>
      <Card description="Queue totals are shown exactly as returned by the admin queue API." title="Queues">
        {opsLoading ? (
          <EmptyState description="Queue data is loading." title="Loading queues" />
        ) : opsError ? (
          <EmptyState description={opsError} title="Queue data unavailable" />
        ) : (
          <AdminQueuesTable queues={queues} />
        )}
      </Card>
    </div>
  );
}
