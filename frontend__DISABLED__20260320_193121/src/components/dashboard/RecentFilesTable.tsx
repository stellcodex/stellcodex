import Link from "next/link";

import { Table } from "@/components/primitives/Table";
import { EmptyState } from "@/components/primitives/EmptyState";
import type { FileRecord } from "@/lib/contracts/ui";
import { formatBytes, formatDateTime } from "@/lib/utils";

import { FileStatusBadge } from "../files/FileStatusBadge";

export interface RecentFilesTableProps {
  files: FileRecord[];
}

export function RecentFilesTable({ files }: RecentFilesTableProps) {
  if (files.length === 0) {
    return <EmptyState description="Uploads and worker outputs will appear here once a file is accepted." title="No recent files" />;
  }

  return (
    <Table>
      <thead className="bg-[var(--background-subtle)] text-left text-xs uppercase tracking-[0.16em] text-[var(--foreground-soft)]">
        <tr>
          <th className="px-4 py-3">File</th>
          <th className="px-4 py-3">Status</th>
          <th className="px-4 py-3">Size</th>
          <th className="px-4 py-3">Updated</th>
          <th className="px-4 py-3" />
        </tr>
      </thead>
      <tbody>
        {files.map((file) => (
          <tr key={file.fileId} className="border-t border-[var(--border-muted)]">
            <td className="px-4 py-3">
              <div className="font-medium">{file.originalName}</div>
              <div className="text-xs text-[var(--foreground-muted)]">{file.fileId}</div>
            </td>
            <td className="px-4 py-3">
              <FileStatusBadge status={file.status} />
            </td>
            <td className="px-4 py-3">{formatBytes(file.sizeBytes)}</td>
            <td className="px-4 py-3">{formatDateTime(file.createdAt)}</td>
            <td className="px-4 py-3 text-right">
              <Link className="text-sm font-medium" href={`/files/${encodeURIComponent(file.fileId)}`}>
                Open
              </Link>
            </td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}
