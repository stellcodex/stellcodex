"use client";

import { AppShell } from "@/components/shell/AppShell";
import { ErrorState } from "@/components/primitives/ErrorState";
import { LoadingSkeleton } from "@/components/primitives/LoadingSkeleton";
import { FilesAdminTable } from "@/components/admin/FilesAdminTable";
import { useAdminQueues } from "@/lib/hooks/useAdminQueues";

export default function AdminFilesPage() {
  const { files, loading, error, refresh } = useAdminQueues();
  return (
    <AppShell title="Admin files" subtitle="Safe file inventory" breadcrumbs={[{ href: "/admin", label: "Admin" }, { label: "Files" }]}>
      {loading ? <LoadingSkeleton label="Loading admin files" /> : null}
      {error ? <ErrorState title="Admin files unavailable" description={error} retryLabel="Retry" onRetry={() => void refresh()} /> : null}
      {!loading && !error ? <FilesAdminTable rows={files} /> : null}
    </AppShell>
  );
}
