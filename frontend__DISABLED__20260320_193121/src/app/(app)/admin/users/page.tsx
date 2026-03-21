"use client";

import { AdminUsersTable } from "@/components/admin/AdminUsersTable";
import { Card } from "@/components/primitives/Card";
import { PageHeader } from "@/components/shell/PageHeader";
import { RouteErrorState } from "@/components/states/RouteErrorState";
import { RouteLoadingState } from "@/components/states/RouteLoadingState";
import { useAdminUsers } from "@/lib/hooks/useAdminUsers";

export default function AdminUsersPage() {
  const { items, loading, error, refresh } = useAdminUsers();
  if (loading) return <RouteLoadingState title="Loading users" />;
  if (error) return <RouteErrorState actionLabel="Retry" description={error} onAction={() => void refresh()} title="Users unavailable" />;
  return (
    <div className="space-y-6">
      <PageHeader subtitle="User operations are rendered only from the supported admin users endpoint." title="Users" />
      <Card title="Users">
        <AdminUsersTable items={items} />
      </Card>
    </div>
  );
}
