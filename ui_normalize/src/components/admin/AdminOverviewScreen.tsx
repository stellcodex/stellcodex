"use client";

import Link from "next/link";

import { Card } from "@/components/primitives/Card";
import { Button } from "@/components/primitives/Button";
import { PageHeader } from "@/components/shell/PageHeader";
import { RouteErrorState } from "@/components/states/RouteErrorState";
import { RouteLoadingState } from "@/components/states/RouteLoadingState";
import { useAdminHealth } from "@/lib/hooks/useAdminHealth";

import { AdminHealthPanel } from "./AdminHealthPanel";

export function AdminOverviewScreen() {
  const { items, loading, error, refresh } = useAdminHealth();

  if (loading) return <RouteLoadingState title="Loading admin overview" />;
  if (error) return <RouteErrorState actionLabel="Retry" description={error} onAction={() => void refresh()} title="Admin unavailable" />;

  return (
    <div className="space-y-6">
      <PageHeader subtitle="Operations" title="Admin" />
      <AdminHealthPanel items={items} />
      <Card title="Routes">
        <div className="space-y-3">
          {[
            ["/admin/health", "Health"],
            ["/admin/queues", "Queues"],
            ["/admin/queues/failed", "Failed jobs"],
            ["/admin/audit", "Audit"],
            ["/admin/users", "Users"],
            ["/admin/files", "Files"],
          ].map(([href, label]) => (
            <Link href={href as string} key={href}>
              <Button className="w-full justify-between" variant="secondary">
                {label}
                <span>Open</span>
              </Button>
            </Link>
          ))}
        </div>
      </Card>
    </div>
  );
}
