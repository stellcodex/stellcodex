"use client";

import { AdminHealthPanel } from "@/components/admin/AdminHealthPanel";
import { PageHeader } from "@/components/shell/PageHeader";
import { RouteErrorState } from "@/components/states/RouteErrorState";
import { RouteLoadingState } from "@/components/states/RouteLoadingState";
import { useAdminHealth } from "@/lib/hooks/useAdminHealth";

export default function AdminHealthPage() {
  const { items, loading, error, refresh } = useAdminHealth();
  if (loading) return <RouteLoadingState title="Loading admin health" />;
  if (error) return <RouteErrorState actionLabel="Retry" description={error} onAction={() => void refresh()} title="Admin health unavailable" />;
  return (
    <div className="space-y-6">
      <PageHeader subtitle="Supported component health only." title="Admin health" />
      <AdminHealthPanel items={items} />
    </div>
  );
}
