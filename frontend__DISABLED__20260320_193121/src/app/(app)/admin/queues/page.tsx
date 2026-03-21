"use client";

import Link from "next/link";

import { AdminFailedJobsTable } from "@/components/admin/AdminFailedJobsTable";
import { AdminQueuesTable } from "@/components/admin/AdminQueuesTable";
import { Button } from "@/components/primitives/Button";
import { Card } from "@/components/primitives/Card";
import { PageHeader } from "@/components/shell/PageHeader";
import { RouteErrorState } from "@/components/states/RouteErrorState";
import { RouteLoadingState } from "@/components/states/RouteLoadingState";
import { useAdminQueues } from "@/lib/hooks/useAdminQueues";

export default function AdminQueuesPage() {
  const { queues, failedJobs, loading, error, refresh } = useAdminQueues();
  if (loading) return <RouteLoadingState title="Loading queues" />;
  if (error) return <RouteErrorState actionLabel="Retry" description={error} onAction={() => void refresh()} title="Queues unavailable" />;
  return (
    <div className="space-y-6">
      <PageHeader
        actions={
          <Link href="/admin/queues/failed">
            <Button variant="secondary">Open failed jobs</Button>
          </Link>
        }
        subtitle="Queue and worker counts from the admin backend surface."
        title="Admin queues"
      />
      <Card title="Queue counts">
        <AdminQueuesTable queues={queues} />
      </Card>
      <Card title="Recent failed jobs">
        <AdminFailedJobsTable items={failedJobs.slice(0, 10)} />
      </Card>
    </div>
  );
}
