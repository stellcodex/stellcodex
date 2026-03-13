import type { QueueSummary } from "@/lib/contracts/admin";
import { Table } from "@/components/primitives/Table";

export interface QueueTableProps {
  queues: QueueSummary[];
}

export function QueueTable({ queues }: QueueTableProps) {
  return (
    <Table
      head={
        <tr>
          <th>Queue</th>
          <th>Queued</th>
          <th>Started</th>
          <th>Failed</th>
        </tr>
      }
      body={
        queues.length > 0 ? (
          queues.map((queue) => (
            <tr key={queue.name}>
              <td>{queue.name}</td>
              <td>{queue.queuedCount}</td>
              <td>{queue.startedCount}</td>
              <td>{queue.failedCount}</td>
            </tr>
          ))
        ) : (
          <tr>
            <td colSpan={4}>No queue data</td>
          </tr>
        )
      }
    />
  );
}
