import Link from "next/link";
import type { ProjectSummary } from "@/lib/contracts/projects";
import { Table } from "@/components/primitives/Table";

export function RecentProjectsTable({
  rows,
  projectHref,
}: {
  rows: ProjectSummary[];
  projectHref?: (projectId: string) => string;
}) {
  return (
    <Table
      head={
        <tr>
          <th>Project</th>
          <th>Files</th>
          <th>Updated</th>
          <th />
        </tr>
      }
      body={
        rows.length > 0 ? (
          rows.map((row) => (
            <tr key={row.projectId}>
              <td>{row.name}</td>
              <td>{row.filesCount || 0}</td>
              <td>{row.updatedAt || "Not available"}</td>
              <td>
                <Link href={projectHref ? projectHref(row.projectId) : `/projects/${row.projectId}`}>Open</Link>
              </td>
            </tr>
          ))
        ) : (
          <tr>
            <td colSpan={4}>No projects found</td>
          </tr>
        )
      }
    />
  );
}
