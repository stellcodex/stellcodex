import Link from "next/link";

import { Card } from "@/components/primitives/Card";
import { EmptyState } from "@/components/primitives/EmptyState";
import type { FileRecord } from "@/lib/contracts/ui";

import { FileStatusBadge } from "../files/FileStatusBadge";

export interface AttentionPanelProps {
  files: FileRecord[];
}

export function AttentionPanel({ files }: AttentionPanelProps) {
  const attentionItems = files.filter((file) => ["failed", "queued", "processing", "running"].includes(file.status.toLowerCase()));

  return (
    <Card description="Operational attention is driven by real upload and worker state. No synthetic KPI layer is shown." title="Attention queue">
      {attentionItems.length === 0 ? (
        <EmptyState description="Nothing currently needs intervention." title="Queue clear" />
      ) : (
        <div className="space-y-3">
          {attentionItems.map((file) => (
            <div key={file.fileId} className="flex items-center justify-between rounded-[var(--radius-md)] border border-[var(--border-muted)] px-4 py-3">
              <div className="space-y-1">
                <div className="text-sm font-medium">{file.originalName}</div>
                <div className="text-xs text-[var(--foreground-muted)]">{file.fileId}</div>
              </div>
              <div className="flex items-center gap-3">
                <FileStatusBadge status={file.status} />
                <Link className="text-sm font-medium" href={`/files/${encodeURIComponent(file.fileId)}`}>
                  Open
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
