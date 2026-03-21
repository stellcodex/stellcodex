import { Button } from "@/components/primitives/Button";
import { EmptyState } from "@/components/primitives/EmptyState";
import { Table } from "@/components/primitives/Table";
import type { ShareRecord } from "@/lib/contracts/ui";
import { formatDateTime } from "@/lib/utils";

import { ShareStatusBadge } from "./ShareStatusBadge";

export interface ShareTableProps {
  shares: ShareRecord[];
  onCopy: (share: ShareRecord) => Promise<void>;
  onOpen: (share: ShareRecord) => void;
  onRevoke: (shareId: string) => Promise<void>;
}

export function ShareTable({ onCopy, onOpen, onRevoke, shares }: ShareTableProps) {
  if (shares.length === 0) {
    return <EmptyState description="Create a share from a file to populate this surface." title="No shares" />;
  }

  return (
    <Table>
      <thead className="bg-[var(--background-subtle)] text-left text-sm text-[var(--foreground-soft)]">
        <tr>
          <th className="px-4 py-3">Token</th>
          <th className="px-4 py-3">Permission</th>
          <th className="px-4 py-3">Expiry</th>
          <th className="px-4 py-3">Status</th>
          <th className="px-4 py-3">File</th>
          <th className="px-4 py-3" />
        </tr>
      </thead>
      <tbody>
        {shares.map((share) => (
          <tr key={share.shareId} className="border-t border-[var(--border-muted)]">
            <td className="px-4 py-3 font-medium">{share.token.slice(0, 12)}...</td>
            <td className="px-4 py-3">{share.permission}</td>
            <td className="px-4 py-3">{formatDateTime(share.expiresAt)}</td>
            <td className="px-4 py-3">
              <ShareStatusBadge status={share.status} />
            </td>
            <td className="px-4 py-3 text-sm text-[var(--foreground-muted)]">{share.fileId || "Derived"}</td>
            <td className="px-4 py-3">
              <div className="flex justify-end gap-2">
                <Button onClick={() => void onCopy(share)} size="sm">
                  Copy
                </Button>
                <Button onClick={() => onOpen(share)} size="sm">
                  Open
                </Button>
                <Button onClick={() => void onRevoke(share.shareId)} size="sm" variant="danger">
                  Revoke
                </Button>
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </Table>
  );
}
