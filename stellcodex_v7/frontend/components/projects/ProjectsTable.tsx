import Link from "next/link";
import type { ProjectSummary } from "@/lib/contracts/projects";
import { Table } from "@/components/primitives/Table";
import { Badge } from "@/components/primitives/Badge";

export interface ProjectsTableProps {
  rows: ProjectSummary[];
}

export function ProjectsTable({ rows }: ProjectsTableProps) {
  return (
    <Table
      head={
        <tr>
          <th>Project</th>
          <th>Files</th>
          <th>Ready</th>
          <th>Processing</th>
          <th />
        </tr>
      }
      body={
        rows.length > 0 ? (
          rows.map((row) => (
            <tr key={row.projectId}>
              <td>
                <div className="sc-stack">
                  <strong>{row.name}</strong>
                  {row.description ? <span className="sc-muted">{row.description}</span> : null}
                </div>
              </td>
              <td>{row.filesCount || 0}</td>
              <td><Badge variant="success">{row.readyCount || 0}</Badge></td>
              <td><Badge variant="warning">{row.processingCount || 0}</Badge></td>
              <td>
                <Link href={`/projects/${row.projectId}`}>Open</Link>
              </td>
            </tr>
          ))
        ) : (
          <tr>
            <td colSpan={5}>No projects found</td>
          </tr>
        )
      }
    />
  );
}
