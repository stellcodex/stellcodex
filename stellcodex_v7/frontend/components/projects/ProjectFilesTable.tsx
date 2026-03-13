import Link from "next/link";
import type { FileSummary } from "@/lib/contracts/files";
import { Table } from "@/components/primitives/Table";
import { FileStatusBadge } from "@/components/status/FileStatusBadge";

export interface ProjectFilesTableProps {
  files: FileSummary[];
}

export function ProjectFilesTable({ files }: ProjectFilesTableProps) {
  return (
    <Table
      head={
        <tr>
          <th>File</th>
          <th>Status</th>
          <th>Type</th>
          <th />
        </tr>
      }
      body={
        files.length > 0 ? (
          files.map((file) => (
            <tr key={file.fileId}>
              <td>{file.fileName}</td>
              <td><FileStatusBadge status={file.status} /></td>
              <td>{file.mimeType || "Unknown"}</td>
              <td>
                <div className="sc-inline">
                  <Link href={`/files/${file.fileId}`}>File</Link>
                  <Link href={`/files/${file.fileId}/viewer`}>Viewer</Link>
                </div>
              </td>
            </tr>
          ))
        ) : (
          <tr>
            <td colSpan={4}>No files in this project yet</td>
          </tr>
        )
      }
    />
  );
}
