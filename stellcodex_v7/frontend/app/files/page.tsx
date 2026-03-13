"use client";

import { useState } from "react";
import { AppShell } from "@/components/shell/AppShell";
import { AppPage } from "@/components/shell/AppPage";
import { ErrorState } from "@/components/primitives/ErrorState";
import { LoadingSkeleton } from "@/components/primitives/LoadingSkeleton";
import { RecentFilesTable } from "@/components/dashboard/RecentFilesTable";
import { UploadDropzone } from "@/components/dashboard/UploadDropzone";
import { UploadProgressList } from "@/components/dashboard/UploadProgressList";
import { useFilesIndex } from "@/lib/hooks/useFilesIndex";
import { useUpload } from "@/lib/hooks/useUpload";

export default function FilesPage() {
  const { data, loading, error, refresh } = useFilesIndex();
  const { items, startUpload } = useUpload();
  const [uploadError, setUploadError] = useState<string | null>(null);

  async function handleFilesSelected(files: File[]) {
    setUploadError(null);
    for (const file of files) {
      const result = await startUpload(file);
      if (!result) {
        setUploadError("Upload failed.");
      }
    }
    await refresh();
  }

  return (
    <AppShell title="Files" subtitle="Operational file hub" breadcrumbs={[{ label: "Files" }]}>
      <AppPage title="Files" subtitle="Upload, inspect status, and open viewers">
        <UploadDropzone error={uploadError} isUploading={items.some((item) => item.status === "uploading")} onFilesSelected={handleFilesSelected} />
        <UploadProgressList items={items} />
        {loading ? <LoadingSkeleton label="Loading files" /> : null}
        {error ? <ErrorState title="Files unavailable" description={error} retryLabel="Retry" onRetry={() => void refresh()} /> : null}
        {!loading && !error ? <RecentFilesTable rows={data} /> : null}
      </AppPage>
    </AppShell>
  );
}
