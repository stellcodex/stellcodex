"use client";

import Link from "next/link";
import { AppShell } from "@/components/shell/AppShell";
import { AppPage } from "@/components/shell/AppPage";
import { ErrorState } from "@/components/primitives/ErrorState";
import { LoadingSkeleton } from "@/components/primitives/LoadingSkeleton";
import { AdminStatCards } from "@/components/admin/AdminStatCards";
import { HealthSummary } from "@/components/admin/HealthSummary";
import { useAdminHealth } from "@/lib/hooks/useAdminHealth";
import { useAdminQueues } from "@/lib/hooks/useAdminQueues";

export default function AdminPage() {
  const health = useAdminHealth();
  const queues = useAdminQueues();

  const loading = health.loading || queues.loading;
  const error = health.error || queues.error;

  return (
    <AppShell title="Admin" subtitle="Operational admin surfaces" breadcrumbs={[{ label: "Admin" }]}>
      <AppPage title="Admin" subtitle="Safe health, queues, audit, files, and users">
        {loading ? <LoadingSkeleton label="Loading admin summary" /> : null}
        {error ? <ErrorState title="Admin unavailable" description={error} retryLabel="Retry" onRetry={() => { void health.refresh(); void queues.refresh(); }} /> : null}
        {!loading && !error ? (
          <>
            <AdminStatCards
              queues={queues.queues.length}
              failedJobs={queues.failedJobs.length}
              files={queues.files.length}
              users={queues.users.length}
            />
            <HealthSummary data={health.data} />
            <div className="sc-inline">
              <Link href="/admin/health">Health</Link>
              <Link href="/admin/queues">Queues</Link>
              <Link href="/admin/queues/failed">Failed jobs</Link>
              <Link href="/admin/audit">Audit</Link>
              <Link href="/admin/users">Users</Link>
              <Link href="/admin/files">Files</Link>
            </div>
          </>
        ) : null}
      </AppPage>
    </AppShell>
  );
}
