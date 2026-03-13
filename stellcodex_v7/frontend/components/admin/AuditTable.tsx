import type { AuditEventSummary } from "@/lib/contracts/admin";
import { Table } from "@/components/primitives/Table";

export interface AuditTableProps {
  rows: AuditEventSummary[];
}

export function AuditTable({ rows }: AuditTableProps) {
  return (
    <Table
      head={
        <tr>
          <th>Timestamp</th>
          <th>Actor</th>
          <th>Action</th>
          <th>Target</th>
          <th>Meta</th>
        </tr>
      }
      body={
        rows.length > 0 ? (
          rows.map((row) => (
            <tr key={row.id}>
              <td>{row.timestamp}</td>
              <td>{row.actor || "system"}</td>
              <td>{row.action}</td>
              <td>{row.targetId || row.targetType || "n/a"}</td>
              <td>{row.safeMetaPreview || "No meta"}</td>
            </tr>
          ))
        ) : (
          <tr>
            <td colSpan={5}>No audit events</td>
          </tr>
        )
      }
    />
  );
}
