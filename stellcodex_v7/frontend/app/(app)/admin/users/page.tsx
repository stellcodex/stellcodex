"use client";

import { AppShell } from "@/components/shell/AppShell";
import { ErrorState } from "@/components/primitives/ErrorState";
import { LoadingSkeleton } from "@/components/primitives/LoadingSkeleton";
import { UsersTable } from "@/components/admin/UsersTable";
import { useAdminQueues } from "@/lib/hooks/useAdminQueues";

export default function AdminUsersPage() {
  const { users, loading, error, refresh } = useAdminQueues();
  return (
    <AppShell title="Users" subtitle="Admin user inventory" breadcrumbs={[{ href: "/admin", label: "Admin" }, { label: "Users" }]}>
      {loading ? <LoadingSkeleton label="Loading users" /> : null}
      {error ? <ErrorState title="Users unavailable" description={error} retryLabel="Retry" onRetry={() => void refresh()} /> : null}
      {!loading && !error ? <UsersTable rows={users} /> : null}
    </AppShell>
  );
}
