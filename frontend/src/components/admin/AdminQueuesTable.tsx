import { EmptyState } from "@/components/primitives/EmptyState";
import { Table } from "@/components/primitives/Table";
import type { AdminQueueRecord } from "@/lib/contracts/ui";

export interface AdminQueuesTableProps {
  queues: AdminQueueRecord[];
}

export function AdminQueuesTable({ queues }: AdminQueuesTableProps) {
  if (queues.length === 0) {
    return <EmptyState description="Queue telemetry is not available." title="No queue data" />;
  }

  return (
    <Table>
      <thead className="bg-[var(--background-subtle)] text-left text-xs uppercase tracking-[0.16em] text-[var(--foreground-soft)]">
        <tr>
          <th className="px-4 py-3">Queue</th>
          <th className="px-4 py-3">Queued</th>
          <th className="px-4 py-3">Started</th>
          <th className="px-4 py-3">Failed</th>
        </tr>
      </thead>
      <tbody>
        {queues.map((queue) => (
          <tr key={queue.name} className="border-t border-[var(--border-muted)]">
            <td className="px-4 py-3 font-medium">{queue.name}</td>
            <td className="px-4 py-3">{queue.queuedCount}</td>
            <td className="px-4 py-3">{queue.startedCount}</td>
            <td className="px-4 py-3">{queue.failedCount}</td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}
