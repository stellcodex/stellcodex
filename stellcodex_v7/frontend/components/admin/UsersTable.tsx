import type { UserSummary } from "@/lib/contracts/admin";
import { Table } from "@/components/primitives/Table";
import { Badge } from "@/components/primitives/Badge";

export interface UsersTableProps {
  rows: UserSummary[];
}

export function UsersTable({ rows }: UsersTableProps) {
  return (
    <Table
      head={
        <tr>
          <th>Email</th>
          <th>Role</th>
          <th>Status</th>
        </tr>
      }
      body={
        rows.length > 0 ? (
          rows.map((row) => (
            <tr key={row.id}>
              <td>{row.email}</td>
              <td>{row.role}</td>
              <td><Badge variant={row.suspended ? "danger" : "success"}>{row.suspended ? "Suspended" : "Active"}</Badge></td>
            </tr>
          ))
        ) : (
          <tr>
            <td colSpan={3}>No users found</td>
          </tr>
        )
      }
    />
  );
}
