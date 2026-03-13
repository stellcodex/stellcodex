"use client";

import { AppShell } from "@/components/shell/AppShell";
import { ErrorState } from "@/components/primitives/ErrorState";
import { LoadingSkeleton } from "@/components/primitives/LoadingSkeleton";
import { QueueTable } from "@/components/admin/QueueTable";
import { useAdminQueues } from "@/lib/hooks/useAdminQueues";

export default function AdminQueuesPage() {
  const { queues, loading, error, refresh } = useAdminQueues();
  return (
    <AppShell title="Queues" subtitle="Queue depth and running jobs" breadcrumbs={[{ href: "/admin", label: "Admin" }, { label: "Queues" }]}>
      {loading ? <LoadingSkeleton label="Loading queues" /> : null}
      {error ? <ErrorState title="Queues unavailable" description={error} retryLabel="Retry" onRetry={() => void refresh()} /> : null}
      {!loading && !error ? <QueueTable queues={queues} /> : null}
    </AppShell>
  );
}
