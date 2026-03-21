import { EmptyState } from "@/components/primitives/EmptyState";
import { Panel } from "@/components/primitives/Panel";

export interface VersionsTableProps {
  supported: boolean;
}

export function VersionsTable({ supported }: VersionsTableProps) {
  return (
    <Panel description="Version history must come from backend truth. No synthetic revision chain is shown." title="Versions">
      {supported ? (
        <div className="text-sm text-[var(--foreground-muted)]">Version support is available.</div>
      ) : (
        <EmptyState
          description="The current backend contract does not expose a file versions endpoint, so version history remains fail-closed."
          title="Version history unavailable"
        />
      )}
    </Panel>
  );
}
