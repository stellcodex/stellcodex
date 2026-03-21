import { EmptyState } from "@/components/primitives/EmptyState";
import { Table } from "@/components/primitives/Table";
import type { AdminAuditRecord } from "@/lib/contracts/ui";
import { formatDateTime } from "@/lib/utils";

export interface AdminAuditTableProps {
  items: AdminAuditRecord[];
}

export function AdminAuditTable({ items }: AdminAuditTableProps) {
  if (items.length === 0) {
    return <EmptyState description="No audit records were returned." title="No audit events" />;
  }

  return (
    <Table>
      <thead className="bg-[var(--background-subtle)] text-left text-xs uppercase tracking-[0.16em] text-[var(--foreground-soft)]">
        <tr>
          <th className="px-4 py-3">Event</th>
          <th className="px-4 py-3">Actor</th>
          <th className="px-4 py-3">File</th>
          <th className="px-4 py-3">Data</th>
          <th className="px-4 py-3">Created</th>
        </tr>
      </thead>
      <tbody>
        {items.map((item) => (
          <tr key={item.id} className="border-t border-[var(--border-muted)] align-top">
            <td className="px-4 py-3 font-medium">{item.eventType}</td>
            <td className="px-4 py-3 text-[var(--foreground-muted)]">{item.actorUserId || item.actorAnonSub || "System"}</td>
            <td className="px-4 py-3 text-[var(--foreground-muted)]">{item.fileId || "N/A"}</td>
            <td className="max-w-[320px] px-4 py-3 text-xs text-[var(--foreground-muted)]">
              <pre className="whitespace-pre-wrap">{JSON.stringify(item.data, null, 2)}</pre>
            </td>
            <td className="px-4 py-3">{formatDateTime(item.createdAt)}</td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}
