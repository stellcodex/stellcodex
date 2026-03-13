import type { ShareSummary } from "@/lib/contracts/shares";
import { Panel } from "@/components/primitives/Panel";
import { ShareTable } from "@/components/shares/ShareTable";

export interface FileSharesPanelProps {
  shares: ShareSummary[];
  onRevoke: (shareId: string) => void;
}

export function FileSharesPanel({ shares, onRevoke }: FileSharesPanelProps) {
  return (
    <Panel title="Shares">
      <ShareTable shares={shares} onRevoke={onRevoke} />
    </Panel>
  );
}
