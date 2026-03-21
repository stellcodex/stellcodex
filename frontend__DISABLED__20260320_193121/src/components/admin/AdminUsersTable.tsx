import { EmptyState } from "@/components/primitives/EmptyState";
import { Table } from "@/components/primitives/Table";
import type { AdminUserRecord } from "@/lib/contracts/ui";
import { formatDateTime } from "@/lib/utils";

export interface AdminUsersTableProps {
  items: AdminUserRecord[];
}

export function AdminUsersTable({ items }: AdminUsersTableProps) {
  if (items.length === 0) {
    return <EmptyState description="No user rows were returned." title="No users" />;
  }

  return (
    <Table>
      <thead className="bg-[var(--background-subtle)] text-left text-xs uppercase tracking-[0.16em] text-[var(--foreground-soft)]">
        <tr>
          <th className="px-4 py-3">Email</th>
          <th className="px-4 py-3">Role</th>
          <th className="px-4 py-3">Suspended</th>
          <th className="px-4 py-3">Created</th>
        </tr>
      </thead>
      <tbody>
        {items.map((item) => (
          <tr key={item.id} className="border-t border-[var(--border-muted)]">
            <td className="px-4 py-3 font-medium">{item.email}</td>
            <td className="px-4 py-3">{item.role}</td>
            <td className="px-4 py-3">{item.suspended ? "Yes" : "No"}</td>
            <td className="px-4 py-3">{formatDateTime(item.createdAt)}</td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}
