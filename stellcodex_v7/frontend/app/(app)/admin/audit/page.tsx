"use client";

import { AppShell } from "@/components/shell/AppShell";
import { ErrorState } from "@/components/primitives/ErrorState";
import { LoadingSkeleton } from "@/components/primitives/LoadingSkeleton";
import { AuditTable } from "@/components/admin/AuditTable";
import { useAdminQueues } from "@/lib/hooks/useAdminQueues";

export default function AdminAuditPage() {
  const { audit, loading, error, refresh } = useAdminQueues();
  return (
    <AppShell title="Audit" subtitle="Safe audit trail" breadcrumbs={[{ href: "/admin", label: "Admin" }, { label: "Audit" }]}>
      {loading ? <LoadingSkeleton label="Loading audit" /> : null}
      {error ? <ErrorState title="Audit unavailable" description={error} retryLabel="Retry" onRetry={() => void refresh()} /> : null}
      {!loading && !error ? <AuditTable rows={audit} /> : null}
    </AppShell>
  );
}
