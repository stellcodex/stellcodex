"use client";

import * as React from "react";
import { useRouter } from "next/navigation";

import { Card } from "@/components/primitives/Card";
import { PageHeader } from "@/components/shell/PageHeader";
import { RouteErrorState } from "@/components/states/RouteErrorState";
import { RouteLoadingState } from "@/components/states/RouteLoadingState";
import { listFiles } from "@/lib/api/files";
import { mapFileRecord } from "@/lib/mappers/fileMappers";
import { useProjects } from "@/lib/hooks/useProjects";
import { useUpload } from "@/lib/hooks/useUpload";

import { AttentionPanel } from "./AttentionPanel";
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

  React.useEffect(() => {
    void refreshFiles();
  }, [refreshFiles]);

  if (projectsLoading && filesLoading) {
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
        }}
        title="Dashboard unavailable"
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        subtitle="Upload files, inspect recent work, and handle operational attention without leaving the manufacturing flow."
        title="Dashboard"
      />
      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.15fr)_380px]">
        <div className="space-y-6">
          <UploadDropzone
            onUpload={async (file) => {
              const fileId = await upload(file);
              if (fileId) router.push(`/files/${encodeURIComponent(fileId)}`);
            }}
            uploads={items}
          />
          <Card description="Recent project workspaces resolved from the live project contract." title="Recent workspaces">
            <RecentProjectsTable projects={projects.slice(0, 6)} />
          </Card>
          <Card description="Latest files and worker outputs." title="Recent files">
            <RecentFilesTable files={files} />
          </Card>
        </div>
        <AttentionPanel files={files} />
      </div>
    </div>
  );
}
