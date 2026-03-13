import type { FileVersionSummary } from "@/lib/contracts/files";
import { Table } from "@/components/primitives/Table";
import { Badge } from "@/components/primitives/Badge";

export interface FileVersionsTableProps {
  versions: FileVersionSummary[];
}

export function FileVersionsTable({ versions }: FileVersionsTableProps) {
  return (
    <Table
      head={
        <tr>
          <th>Version</th>
          <th>Status</th>
          <th>Created</th>
        </tr>
      }
      body={
        versions.length > 0 ? (
          versions.map((version) => (
            <tr key={version.versionId}>
              <td>
                <div className="sc-inline">
                  <span>{version.label}</span>
                  {version.isCurrent ? <Badge variant="info">Current</Badge> : null}
                </div>
              </td>
              <td>{version.status || "Unknown"}</td>
              <td>{version.createdAt || "Not available"}</td>
            </tr>
          ))
        ) : (
          <tr>
            <td colSpan={3}>No versions available</td>
          </tr>
        )
      }
    />
  );
}
