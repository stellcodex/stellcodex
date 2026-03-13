import { Table } from "@/components/primitives/Table";
import { JobStatusBadge } from "@/components/status/JobStatusBadge";

export type RecentJobRow = {
  id: string;
  fileId?: string | null;
  stage?: string | null;
  status: string;
  createdAt?: string | null;
};

export interface RecentJobsTableProps {
  rows: RecentJobRow[];
}

export function RecentJobsTable({ rows }: RecentJobsTableProps) {
  return (
    <Table
      head={
        <tr>
          <th>Job</th>
          <th>Stage</th>
          <th>Status</th>
          <th>Created</th>
        </tr>
      }
      body={
        rows.length > 0 ? (
          rows.map((row) => (
            <tr key={row.id}>
              <td>{row.fileId || row.id}</td>
              <td>{row.stage || "Pending"}</td>
              <td>
                <JobStatusBadge status={row.status} />
              </td>
              <td>{row.createdAt || "Not available"}</td>
            </tr>
          ))
        ) : (
          <tr>
            <td colSpan={4}>No jobs found</td>
          </tr>
        )
      }
    />
  );
}
