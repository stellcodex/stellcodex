import type { AdminFileSummary } from "@/lib/contracts/admin";
import { Table } from "@/components/primitives/Table";
import { FileStatusBadge } from "@/components/status/FileStatusBadge";

export interface FilesAdminTableProps {
  rows: AdminFileSummary[];
}

export function FilesAdminTable({ rows }: FilesAdminTableProps) {
  return (
    <Table
      head={
        <tr>
          <th>File</th>
          <th>Status</th>
          <th>Visibility</th>
          <th>Owner</th>
        </tr>
      }
      body={
        rows.length > 0 ? (
          rows.map((row) => (
            <tr key={row.fileId}>
              <td>{row.fileName}</td>
              <td><FileStatusBadge status={row.status} /></td>
              <td>{row.visibility || "n/a"}</td>
              <td>{row.ownerLabel || "n/a"}</td>
            </tr>
          ))
        ) : (
          <tr>
            <td colSpan={4}>No files found</td>
          </tr>
        )
      }
    />
  );
}
