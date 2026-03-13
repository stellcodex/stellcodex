"use client";

import { useState } from "react";
import type { ShareSummary } from "@/lib/contracts/shares";
import { Table } from "@/components/primitives/Table";
import { SharePermissionsBadge } from "@/components/shares/SharePermissionsBadge";
import { ShareExpiryBadge } from "@/components/shares/ShareExpiryBadge";
import { ShareStatusBadge } from "@/components/shares/ShareStatusBadge";
import { ShareRevokeDialog } from "@/components/shares/ShareRevokeDialog";

export interface ShareTableProps {
  shares: ShareSummary[];
  onRevoke: (shareId: string) => void;
}

export function ShareTable({ shares, onRevoke }: ShareTableProps) {
  const [activeShareId, setActiveShareId] = useState<string | null>(null);
  return (
    <>
      <Table
        head={
          <tr>
            <th>Target</th>
            <th>Permission</th>
            <th>Expiry</th>
            <th>Status</th>
            <th />
          </tr>
        }
        body={
          shares.length > 0 ? (
            shares.map((share) => (
              <tr key={share.shareId}>
                <td>{share.targetName}</td>
                <td><SharePermissionsBadge permission={share.permission} /></td>
                <td><ShareExpiryBadge expiresAt={share.expiresAt} /></td>
                <td><ShareStatusBadge status={share.status} /></td>
                <td>
                  <div className="sc-inline">
                    {share.publicUrl ? <a href={share.publicUrl} target="_blank" rel="noreferrer">Open</a> : null}
                    <button type="button" onClick={() => setActiveShareId(share.shareId)}>Revoke</button>
                  </div>
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={5}>No shares found</td>
            </tr>
          )
        }
      />
      <ShareRevokeDialog
        open={Boolean(activeShareId)}
        onCancel={() => setActiveShareId(null)}
        onConfirm={() => {
          if (activeShareId) onRevoke(activeShareId);
          setActiveShareId(null);
        }}
      />
    </>
  );
}
