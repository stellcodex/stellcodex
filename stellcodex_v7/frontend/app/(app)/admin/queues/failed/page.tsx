"use client";

import { AppShell } from "@/components/shell/AppShell";
import { ErrorState } from "@/components/primitives/ErrorState";
import { LoadingSkeleton } from "@/components/primitives/LoadingSkeleton";
import { FailedJobsTable } from "@/components/admin/FailedJobsTable";
import { useAdminQueues } from "@/lib/hooks/useAdminQueues";

export default function AdminFailedJobsPage() {
  const { failedJobs, loading, error, refresh } = useAdminQueues();
  return (
    <AppShell
      title="Failed jobs"
      subtitle="Recent failed queue items"
      breadcrumbs={[{ href: "/admin", label: "Admin" }, { href: "/admin/queues", label: "Queues" }, { label: "Failed" }]}
    >
      {loading ? <LoadingSkeleton label="Loading failed jobs" /> : null}
      {error ? <ErrorState title="Failed jobs unavailable" description={error} retryLabel="Retry" onRetry={() => void refresh()} /> : null}
      {!loading && !error ? <FailedJobsTable rows={failedJobs} /> : null}
    </AppShell>
  );
}
