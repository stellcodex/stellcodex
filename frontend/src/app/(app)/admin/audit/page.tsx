"use client";

import { AdminAuditTable } from "@/components/admin/AdminAuditTable";
import { Card } from "@/components/primitives/Card";
import { PageHeader } from "@/components/shell/PageHeader";
import { RouteErrorState } from "@/components/states/RouteErrorState";
import { RouteLoadingState } from "@/components/states/RouteLoadingState";
import { useAdminAudit } from "@/lib/hooks/useAdminAudit";

export default function AdminAuditPage() {
  const { items, loading, error, refresh } = useAdminAudit();
  if (loading) return <RouteLoadingState title="Loading audit" />;
  if (error) return <RouteErrorState actionLabel="Retry" description={error} onAction={() => void refresh()} title="Audit unavailable" />;
  return (
    <div className="space-y-6">
      <PageHeader subtitle="Audit data is sanitized for storage and secret leaks before rendering." title="Audit" />
      <Card title="Audit events">
        <AdminAuditTable items={items} />
      </Card>
    </div>
  );
}
