"use client";

import { AdminFilesTable } from "@/components/admin/AdminFilesTable";
import { Card } from "@/components/primitives/Card";
import { PageHeader } from "@/components/shell/PageHeader";
import { RouteErrorState } from "@/components/states/RouteErrorState";
import { RouteLoadingState } from "@/components/states/RouteLoadingState";
import { useAdminFiles } from "@/lib/hooks/useAdminFiles";

export default function AdminFilesPage() {
  const { items, loading, error, refresh } = useAdminFiles();
  if (loading) return <RouteLoadingState title="Loading admin files" />;
  if (error) return <RouteErrorState actionLabel="Retry" description={error} onAction={() => void refresh()} title="Admin files unavailable" />;
  return (
    <div className="space-y-6">
      <PageHeader subtitle="Admin file listings stay dense and safe: no bucket names or storage keys are shown." title="Files" />
      <Card title="Files">
        <AdminFilesTable items={items} />
      </Card>
    </div>
  );
}
