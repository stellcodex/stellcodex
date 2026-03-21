"use client";

import { AdminFailedJobsTable } from "@/components/admin/AdminFailedJobsTable";
import { Card } from "@/components/primitives/Card";
import { PageHeader } from "@/components/shell/PageHeader";
import { RouteErrorState } from "@/components/states/RouteErrorState";
import { RouteLoadingState } from "@/components/states/RouteLoadingState";
import { useAdminQueues } from "@/lib/hooks/useAdminQueues";

export default function AdminFailedJobsPage() {
  const { failedJobs, loading, error, refresh } = useAdminQueues();
  if (loading) return <RouteLoadingState title="Loading failed jobs" />;
  if (error) return <RouteErrorState actionLabel="Retry" description={error} onAction={() => void refresh()} title="Failed jobs unavailable" />;
  return (
    <div className="space-y-6">
      <PageHeader subtitle="Queue failures are shown from the live failed-job endpoint." title="Failed jobs" />
      <Card title="Failed jobs">
        <AdminFailedJobsTable items={failedJobs} />
      </Card>
    </div>
  );
}
