import { Panel } from "@/components/primitives/Panel";

export interface ActivityEvidencePanelProps {
  createdAt: string;
  status: string;
  shareCount: number;
}

export function ActivityEvidencePanel({ createdAt, shareCount, status }: ActivityEvidencePanelProps) {
  return (
    <Panel description="Evidence stays limited to safely supported file workflow facts." title="Activity and evidence">
      <div className="space-y-3 text-sm">
        <div className="flex justify-between">
          <span className="text-[var(--foreground-soft)]">File created</span>
          <span className="font-medium">{createdAt}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-[var(--foreground-soft)]">Current status</span>
          <span className="font-medium">{status}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-[var(--foreground-soft)]">Active shares</span>
          <span className="font-medium">{shareCount}</span>
        </div>
        <div className="rounded-[var(--radius-md)] border border-dashed border-[var(--border-default)] px-3 py-3 text-xs text-[var(--foreground-muted)]">
          A full evidence timeline is not exposed by the current backend contract, so this panel remains limited to safely supported workflow facts.
        </div>
      </div>
    </Panel>
  );
}
