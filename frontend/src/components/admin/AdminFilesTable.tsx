import Link from "next/link";

import { EmptyState } from "@/components/primitives/EmptyState";
import { Table } from "@/components/primitives/Table";
import type { AdminFileRecord } from "@/lib/contracts/ui";
import { formatDateTime } from "@/lib/utils";

import { FileStatusBadge } from "../files/FileStatusBadge";

export interface AdminFilesTableProps {
  items: AdminFileRecord[];
}

export function AdminFilesTable({ items }: AdminFilesTableProps) {
  if (items.length === 0) {
    return <EmptyState description="No admin file rows were returned." title="No files" />;
  }

  return (
    <Table>
      <thead className="bg-[var(--background-subtle)] text-left text-xs uppercase tracking-[0.16em] text-[var(--foreground-soft)]">
        <tr>
          <th className="px-4 py-3">File</th>
          <th className="px-4 py-3">Status</th>
          <th className="px-4 py-3">Visibility</th>
          <th className="px-4 py-3">Owner</th>
          <th className="px-4 py-3">Created</th>
        </tr>
      </thead>
      <tbody>
        {items.map((item) => (
          <tr key={item.fileId} className="border-t border-[var(--border-muted)]">
            <td className="px-4 py-3">
              <Link className="font-medium" href={`/files/${encodeURIComponent(item.fileId)}`}>
                {item.originalFilename}
              </Link>
              <div className="text-xs text-[var(--foreground-muted)]">{item.fileId}</div>
            </td>
            <td className="px-4 py-3">
              <FileStatusBadge status={item.status} />
            </td>
            <td className="px-4 py-3">{item.visibility}</td>
            <td className="px-4 py-3 text-[var(--foreground-muted)]">{item.ownerUserId || item.ownerAnonSub || "N/A"}</td>
            <td className="px-4 py-3">{formatDateTime(item.createdAt)}</td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}
