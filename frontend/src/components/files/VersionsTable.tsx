import { ErrorState } from "@/components/primitives/ErrorState";
import { EmptyState } from "@/components/primitives/EmptyState";
import { LoadingSkeleton } from "@/components/primitives/LoadingSkeleton";
import { Panel } from "@/components/primitives/Panel";
import { Table } from "@/components/primitives/Table";
import type { FileVersionRecord } from "@/lib/contracts/ui";
import { formatBytes, formatDateTime } from "@/lib/utils";

import { FileStatusBadge } from "./FileStatusBadge";

export interface VersionsTableProps {
  supported?: boolean;
  items?: FileVersionRecord[];
  loading?: boolean;
  error?: string | null;
  onRetry?: () => void;
}

export function VersionsTable({
  supported = true,
  items,
  loading = false,
  error = null,
  onRetry,
}: VersionsTableProps) {
  return (
    <Panel description="Version history must come from backend truth. No synthetic revision chain is shown." title="Versions">
      {!supported ? (
        <EmptyState
          description="The current backend contract does not expose a file versions endpoint, so version history remains fail-closed."
          title="Version history unavailable"
        />
      ) : error ? (
        <ErrorState actionLabel={onRetry ? "Retry" : undefined} description={error} onAction={onRetry} title="Version history unavailable" />
      ) : loading ? (
        <div className="space-y-3">
          <LoadingSkeleton className="h-12 w-full" />
          <LoadingSkeleton className="h-12 w-full" />
          <LoadingSkeleton className="h-12 w-full" />
        </div>
      ) : Array.isArray(items) ? (
        items.length > 0 ? (
          <Table>
            <thead className="bg-[var(--background-subtle)] text-left text-xs uppercase tracking-[0.16em] text-[var(--foreground-soft)]">
              <tr>
                <th className="px-4 py-3">Version</th>
                <th className="px-4 py-3">File</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Size</th>
                <th className="px-4 py-3">Created</th>
                <th className="px-4 py-3">Current</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} className="border-t border-[var(--border-muted)]">
                  <td className="px-4 py-3 font-medium">V{item.versionNumber}</td>
                  <td className="px-4 py-3">
                    <div className="font-medium text-[var(--foreground-strong)]">{item.originalName}</div>
                    <div className="text-xs text-[var(--foreground-muted)]">{item.contentType}</div>
                  </td>
                  <td className="px-4 py-3">
                    <FileStatusBadge status={item.status} />
                  </td>
                  <td className="px-4 py-3">{formatBytes(item.sizeBytes)}</td>
                  <td className="px-4 py-3">
                    <div>{formatDateTime(item.createdAt)}</div>
                    {item.createdBy ? <div className="text-xs text-[var(--foreground-muted)]">{item.createdBy}</div> : null}
                  </td>
                  <td className="px-4 py-3 font-medium">{item.isCurrent ? "Current" : "Archived"}</td>
                </tr>
              ))}
            </tbody>
          </Table>
        ) : (
          <EmptyState
            description="The backend version contract is active, but no version rows were returned for this file yet."
            title="No version rows"
          />
        )
      ) : (
        <div className="text-sm text-[var(--foreground-muted)]">
          Version support is available. Open the dedicated versions route to inspect history or upload a new version.
        </div>
      )}
    </Panel>
  );
}
