"use client";

import { useParams } from "next/navigation";
import { AppShell } from "@/components/shell/AppShell";
import { FileVersionsTable } from "@/components/files/FileVersionsTable";
import { LoadingSkeleton } from "@/components/primitives/LoadingSkeleton";
import { ErrorState } from "@/components/primitives/ErrorState";
import { useFileDetail } from "@/lib/hooks/useFileDetail";

export default function FileVersionsPage() {
  const params = useParams<{ fileId: string }>();
  const fileId = params.fileId;
  const { file, versions, loading, error, refresh } = useFileDetail(fileId);
  return (
    <AppShell title="File versions" subtitle="Version history" breadcrumbs={[{ href: "/files", label: "Files" }, { label: file?.fileName || fileId }]}>
      {loading ? <LoadingSkeleton label="Loading versions" /> : null}
      {error ? <ErrorState title="Versions unavailable" description={error} retryLabel="Retry" onRetry={() => void refresh()} /> : null}
      {!loading && !error ? <FileVersionsTable versions={versions} /> : null}
    </AppShell>
  );
}
