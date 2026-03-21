import Link from "next/link";

import { Table } from "@/components/primitives/Table";
import { EmptyState } from "@/components/primitives/EmptyState";
import type { ProjectRecord } from "@/lib/contracts/ui";
import { formatDate } from "@/lib/utils";

export interface RecentProjectsTableProps {
  projects: ProjectRecord[];
}

export function RecentProjectsTable({ projects }: RecentProjectsTableProps) {
  if (projects.length === 0) {
    return <EmptyState description="Projects appear here once uploads are grouped into a manufacturing workstream." title="No recent projects" />;
  }

  return (
    <Table>
      <thead className="bg-[var(--background-subtle)] text-left text-xs uppercase tracking-[0.16em] text-[var(--foreground-soft)]">
        <tr>
          <th className="px-4 py-3">Project</th>
          <th className="px-4 py-3">Files</th>
          <th className="px-4 py-3">Updated</th>
          <th className="px-4 py-3" />
        </tr>
      </thead>
      <tbody>
        {projects.map((project) => (
          <tr key={project.projectId} className="border-t border-[var(--border-muted)]">
            <td className="px-4 py-3">
              <div className="font-medium">{project.name}</div>
              <div className="text-xs text-[var(--foreground-muted)]">{project.projectId}</div>
            </td>
            <td className="px-4 py-3">{project.fileCount}</td>
            <td className="px-4 py-3">{formatDate(project.updatedAt)}</td>
            <td className="px-4 py-3 text-right">
              <Link className="text-sm font-medium text-[var(--foreground-strong)]" href={`/projects/${encodeURIComponent(project.projectId)}`}>
                Open
              </Link>
            </td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}
