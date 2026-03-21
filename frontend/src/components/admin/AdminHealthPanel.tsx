import { Card } from "@/components/primitives/Card";
import { EmptyState } from "@/components/primitives/EmptyState";
import type { AdminHealthRecord } from "@/lib/contracts/ui";

import { FileStatusBadge } from "../files/FileStatusBadge";

export interface AdminHealthPanelProps {
  items: AdminHealthRecord[];
}

export function AdminHealthPanel({ items }: AdminHealthPanelProps) {
  return (
    <Card description="Only supported health components are shown. No secrets or connection strings are exposed." title="Platform health">
      {items.length === 0 ? (
        <EmptyState description="No health response was returned." title="Health unavailable" />
      ) : (
        <div className="grid gap-3 md:grid-cols-2">
          {items.map((item) => (
            <div key={item.component} className="rounded-[var(--radius-md)] border border-[var(--border-muted)] px-4 py-3">
              <div className="text-sm font-medium">{item.component}</div>
              <div className="mt-2">
                <FileStatusBadge status={item.status} />
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
