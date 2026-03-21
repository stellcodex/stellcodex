import Link from "next/link";

import { EmptyState } from "@/components/primitives/EmptyState";
import { Table } from "@/components/primitives/Table";
import type { AdminFailedJobRecord } from "@/lib/contracts/ui";
import { formatDateTime } from "@/lib/utils";

export interface AdminFailedJobsTableProps {
  items: AdminFailedJobRecord[];
}

export function AdminFailedJobsTable({ items }: AdminFailedJobsTableProps) {
  if (items.length === 0) {
    return <EmptyState description="No failed jobs were returned by the backend." title="No failed jobs" />;
  }

  return (
    <Table>
      <thead className="bg-[var(--background-subtle)] text-left text-xs uppercase tracking-[0.16em] text-[var(--foreground-soft)]">
        <tr>
          <th className="px-4 py-3">Job</th>
          <th className="px-4 py-3">File</th>
          <th className="px-4 py-3">Stage</th>
          <th className="px-4 py-3">Error</th>
          <th className="px-4 py-3">Created</th>
        </tr>
      </thead>
      <tbody>
        {items.map((item) => (
          <tr key={item.id} className="border-t border-[var(--border-muted)] align-top">
            <td className="px-4 py-3 font-medium">{item.jobId}</td>
            <td className="px-4 py-3">
              {item.fileId ? <Link href={`/files/${encodeURIComponent(item.fileId)}`}>{item.fileId}</Link> : "N/A"}
            </td>
            <td className="px-4 py-3">{item.stage}</td>
            <td className="px-4 py-3 text-[var(--foreground-muted)]">{item.message}</td>
            <td className="px-4 py-3">{formatDateTime(item.createdAt)}</td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}
