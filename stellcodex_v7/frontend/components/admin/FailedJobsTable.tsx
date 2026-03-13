import type { FailedJobSummary } from "@/lib/contracts/admin";
import { Table } from "@/components/primitives/Table";
import { JobStatusBadge } from "@/components/status/JobStatusBadge";

export interface FailedJobsTableProps {
  rows: FailedJobSummary[];
}

export function FailedJobsTable({ rows }: FailedJobsTableProps) {
  return (
    <Table
      head={
        <tr>
          <th>File</th>
          <th>Stage</th>
          <th>Error</th>
          <th>Created</th>
        </tr>
      }
      body={
        rows.length > 0 ? (
          rows.map((row) => (
            <tr key={row.id}>
              <td>{row.fileId || row.jobId || row.id}</td>
              <td>{row.stage || "Unknown"}</td>
              <td>
                <div className="sc-stack">
                  <JobStatusBadge status="failed" />
                  <span className="sc-muted">{row.message || row.errorClass || "Unknown failure"}</span>
                </div>
              </td>
              <td>{row.createdAt || "Not available"}</td>
            </tr>
          ))
        ) : (
          <tr>
            <td colSpan={4}>No failed jobs</td>
          </tr>
        )
      }
    />
  );
}
