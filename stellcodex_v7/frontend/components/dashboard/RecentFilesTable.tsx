import Link from "next/link";
import type { FileSummary } from "@/lib/contracts/files";
import { Table } from "@/components/primitives/Table";
import { FileStatusBadge } from "@/components/status/FileStatusBadge";

export function RecentFilesTable({
  rows,
  fileHref,
  viewerHref,
}: {
  rows: FileSummary[];
  fileHref?: (fileId: string) => string;
  viewerHref?: (fileId: string) => string;
}) {
  return (
    <Table
      head={
        <tr>
          <th>File</th>
          <th>Status</th>
          <th />
        </tr>
      }
      body={
        rows.length > 0 ? (
          rows.map((row) => (
            <tr key={row.fileId}>
              <td>{row.fileName}</td>
              <td>
                <FileStatusBadge status={row.status} />
              </td>
              <td>
                <div className="sc-inline">
                  <Link href={fileHref ? fileHref(row.fileId) : `/files/${row.fileId}`}>Open</Link>
                  <Link href={viewerHref ? viewerHref(row.fileId) : `/files/${row.fileId}/viewer`}>Viewer</Link>
                </div>
              </td>
            </tr>
          ))
        ) : (
          <tr>
            <td colSpan={3}>No files found</td>
          </tr>
        )
      }
    />
  );
}
