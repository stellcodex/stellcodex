"use client";

import { AppShell } from "@/components/shell/AppShell";
import { HealthSummary } from "@/components/admin/HealthSummary";
import { ErrorState } from "@/components/primitives/ErrorState";
import { LoadingSkeleton } from "@/components/primitives/LoadingSkeleton";
import { useAdminHealth } from "@/lib/hooks/useAdminHealth";

export default function AdminHealthPage() {
  const { data, loading, error, refresh } = useAdminHealth();
  return (
    <AppShell title="Admin health" subtitle="Service and storage health" breadcrumbs={[{ href: "/admin", label: "Admin" }, { label: "Health" }]}>
      {loading ? <LoadingSkeleton label="Loading admin health" /> : null}
      {error ? <ErrorState title="Health unavailable" description={error} retryLabel="Retry" onRetry={() => void refresh()} /> : null}
      {!loading && !error ? <HealthSummary data={data} /> : null}
    </AppShell>
  );
}
